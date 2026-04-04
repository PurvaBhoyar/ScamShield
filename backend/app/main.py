import asyncio
import uuid
import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.schemas.scan import ScanRequest, ScanResponse, Finding
from app.services.rule_engine import RuleEngine
from app.services.scoring import ScoringService
from app.services.threat_intel import ThreatIntelService
from app.services.vector_search import VectorSearchService
from app.services.ocr_service import extract_text_from_image
from app.services.ai_service import analyze_text_with_ai
from app.services.elevenlabs_service import ElevenLabsService
from app.services.platform_verifier import PlatformVerifier
from motor.motor_asyncio import AsyncIOMotorDatabase

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.post("/api/scan", response_model=ScanResponse)
async def perform_parallel_scan(
    type: str = Form(..., pattern="^(url|text|file|audio)$"),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    all_findings = []
    extracted_text = text or ""
    audio_path = None
    
    # --- PHASE 1: Normalization (The Front Door) ---
    if type == "file" and file:
        temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            # Check if it's an image or PDF for OCR
            if file.content_type.startswith("image") or file.filename.endswith(".pdf"):
                extracted_text = extract_text_from_image(temp_path)
            # Check if it's an audio file for ElevenLabs
            elif file.content_type.startswith("audio") or file.filename.endswith((".mp3", ".wav")):
                audio_path = temp_path
        except Exception as e:
            print(f"Extraction Error: {e}")
        finally:
            if not audio_path and os.path.exists(temp_path): os.remove(temp_path)
            
    # --- PHASE 2: Parallel Signal Engine ---
    tasks = []
    
    # Define a helper to run AI and then all Verifiers in parallel
    async def run_ai_and_verify(text: str):
        findings = []
        ai_res = await asyncio.to_thread(analyze_text_with_ai, text)
        if isinstance(ai_res, dict):
            findings.extend(ai_res.get("findings", []))
            company = ai_res.get("company_name", "Unknown Company")
            title = ai_res.get("job_title", "Unknown Title")
            
            # Run all expert verifiers in parallel for this company/job
            expert_results = await asyncio.gather(
                PlatformVerifier.verify_job_publicly(company, title),
                PlatformVerifier.verify_official_careers(company, title),
                PlatformVerifier.verify_company_location(company)
            )
            for res in expert_results:
                findings.extend(res)
        return findings

    # 1. Forensic & Text Logic
    if type == "url" and url:
        tasks.append(asyncio.to_thread(RuleEngine.analyze_url, url))
    
    if extracted_text:
        tasks.append(asyncio.to_thread(RuleEngine.analyze_text, extracted_text))
        ids = ThreatIntelService.extract_identifiers(extracted_text)
        tasks.append(ThreatIntelService.check_blacklist(db, ids))
        tasks.append(VectorSearchService.find_similar_scams(db, extracted_text))
        
        # This task handles both AI Analysis and the subsequent Platform Verification
        tasks.append(run_ai_and_verify(extracted_text))

    # 2. Voice/Convo Intelligence (ElevenLabs)
    if audio_path:
        tasks.append(ElevenLabsService.analyze_audio_conversation(audio_path))

    # EXECUTE ALL IN PARALLEL
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Cleanup audio file after processing
    if audio_path and os.path.exists(audio_path): os.remove(audio_path)

    for res in results:
        if isinstance(res, list):
            all_findings.extend(res)
        elif isinstance(res, dict) and "findings" in res:
            # Handle results from Member 2's AI service dictionary
            all_findings.extend(res["findings"])

    # --- PHASE 3: Verdict ---
    score_result = ScoringService.calculate_score(all_findings)
    recommendations = ScoringService.generate_recommendations(score_result["label"], all_findings)

    response = ScanResponse(
        id=str(uuid.uuid4()),
        score=score_result["score"],
        label=score_result["label"],
        findings=[Finding(**f) for f in all_findings if isinstance(f, dict)],
        evidence=[f["message"] for f in all_findings if isinstance(f, dict) and "message" in f],
        actions=recommendations,
        createdAt=datetime.utcnow()
    )
    
    # Persistence
    await db.scans.insert_one(response.dict())
    return response

@app.get("/health")
async def health(): return {"status": "healthy"}
