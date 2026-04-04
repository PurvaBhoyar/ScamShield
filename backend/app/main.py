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

# Add missing service for URL content extraction
from app.services.url_service import extract_text_from_url

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
    if type == "url" and url:
        # Extract content from the URL as text for secondary analysis
        url_content = await extract_text_from_url(url)
        extracted_text = f"URL Content: {url_content}\n\n{extracted_text}"
        
    elif type == "file" and file:
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
            
    # --- PHASE 2: Parallel Signal Engine (Agentic Orchestration) ---
    tasks = []
    
    # Extract domain from URL for fallback company identification
    fallback_company = None
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc:
            fallback_company = parsed.netloc.replace("www.", "").split(".")[0].capitalize()

    # Define a helper to run AI and then all Verifiers in parallel (Sequential Dependence within Parallelism)
    async def run_ai_and_verify(text: str, domain_fallback: str = None):
        findings = []
        metadata = {"company": "Unknown", "title": "Unknown", "location": "Not Found"}
        
        # 🧠 Brain Agent: Extract entities using Gemini
        ai_res = await asyncio.to_thread(analyze_text_with_ai, text)
        if isinstance(ai_res, dict):
            # Include soft findings from AI analysis (Urgency, Tone, etc.)
            findings.extend(ai_res.get("findings", []))
            
            company = ai_res.get("company_name", "Unknown Company")
            if company == "Unknown" or company == "Unknown Company":
                company = domain_fallback or "Unknown Company"
            
            metadata["company"] = company
            metadata["title"] = ai_res.get("job_title", "Unknown Title")
            
            # 🕵️ Research Agents: Launch deep-web verification in parallel
            expert_results = await asyncio.gather(
                PlatformVerifier.verify_job_publicly(company, metadata["title"]),
                PlatformVerifier.verify_official_careers(company, metadata["title"]),
                PlatformVerifier.verify_company_location(company),
                return_exceptions=True
            )
            for res in expert_results:
                if isinstance(res, list):
                    for f in res:
                        findings.append(f)
                        if f.get("type") == "company_location_found":
                            metadata["location"] = f.get("message", "").split(": ")[-1]
        
        return {"findings": findings, "metadata": metadata}

    # 1. Forensic & Text Logic Tasks
    if type == "url" and url:
        tasks.append(asyncio.to_thread(RuleEngine.analyze_url, url))
    
    if extracted_text:
        # Rule-based text analysis (Blacklist words, patterns)
        tasks.append(asyncio.to_thread(RuleEngine.analyze_text, extracted_text))
        
        # Threat Intel: DB Lookup for UPI/Phone IDs
        ids = ThreatIntelService.extract_identifiers(extracted_text)
        tasks.append(ThreatIntelService.check_blacklist(db, ids))
        
        # Vector Search: Template match in MongoDB
        tasks.append(VectorSearchService.find_similar_scams(db, extracted_text))
        
        # Agentic Research Flow (Starts after AI identifies company)
        tasks.append(run_ai_and_verify(extracted_text, fallback_company))

    # 2. Voice Intelligence Task
    if audio_path:
        tasks.append(ElevenLabsService.analyze_audio_conversation(audio_path))

    # --- EXECUTE ALL AGENTS IN PARALLEL ---
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Cleanup audio file after processing
    if audio_path and os.path.exists(audio_path): os.remove(audio_path)

    metadata = {"company": "Unknown", "title": "Unknown", "location": "Not Found"}
    for res in results:
        if isinstance(res, list):
            all_findings.extend(res)
        elif isinstance(res, dict):
            if "findings" in res:
                all_findings.extend(res["findings"])
            if "metadata" in res:
                metadata.update(res["metadata"])

    # --- PHASE 3: Multi-Factor Verdict ---
    score_result = ScoringService.calculate_score(all_findings)
    recommendations = ScoringService.generate_recommendations(score_result["label"], all_findings)

    response = ScanResponse(
        id=str(uuid.uuid4()),
        company_name=metadata["company"],
        job_title=metadata["title"],
        location=metadata["location"],
        score=score_result["score"],
        label=score_result["label"],
        findings=[Finding(**f) for f in all_findings if isinstance(f, dict)],
        evidence=[f["message"] for f in all_findings if isinstance(f, dict) and "message" in f],
        actions=recommendations,
        createdAt=datetime.utcnow()
    )
    
    # Persistence
    if db is not None:
        try:
            await db.scans.insert_one(response.dict())
        except Exception as e:
            print(f"DB Insert Error: {e}")
    else:
        print("Warning: Database not connected. Result not saved.")
        
    return response

@app.get("/health")
async def health(): return {"status": "healthy"}
