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
from app.schemas.scan import ScanRequest, ScanResponse, Finding, ScoreBreakdown
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
from app.services.domain_service import analyze_domain
from app.services.verification_service import run_verification
from app.services.verification_layers import EightLayerVerifier
from app.core.utils import generate_request_hash

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
    refresh: bool = Form(False),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # --- PHASE 0: Caching Check ---
    file_content = None
    if file:
        file_content = await file.read()
        await file.seek(0) # Reset pointer for later use
    
    request_hash = generate_request_hash(type, url, text, file_content)
    
    if db is not None and not refresh:
        cached_result = await db.scans.find_one({"request_hash": request_hash})
        if cached_result:
            # Cache any valid result (has label) - even Safe results
            if cached_result.get("label"):
                print(f"Cache Hit for {type}: {request_hash}")
                cached_result.pop("_id", None)
                return ScanResponse(**cached_result)
            else:
                print(f"Invalid cache for {request_hash}, re-scanning...")

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
        
        # 🧠 Brain Agent: Extract entities using Groq/Gemini
        ai_res = await asyncio.to_thread(analyze_text_with_ai, text)
        if isinstance(ai_res, dict):
            # Include soft findings from AI analysis (Urgency, Tone, etc.)
            findings.extend(ai_res.get("findings", []))
            
            company = ai_res.get("company_name", "Unknown Company")
            if company == "Unknown" or company == "Unknown Company":
                company = domain_fallback or "Unknown Company"
            
            metadata["company"] = company
            metadata["title"] = ai_res.get("job_title", "Unknown Title")
            
            # 🕵️ Professional 8-Layer Verification (Evidence-First)
            # This replaces the old expert_results logic with the new standard
            layer_res = await EightLayerVerifier.verify_all(
                text, url, company, metadata["title"], metadata["location"]
            )
            
            if "findings" in layer_res:
                findings.extend(layer_res["findings"])
            if "metadata" in layer_res:
                # Update location if found in layers
                if layer_res["metadata"].get("location") and layer_res["metadata"]["location"] != "Not Found":
                    metadata["location"] = layer_res["metadata"]["location"]
        
        return {"findings": findings, "metadata": metadata}

    # 1. Forensic & Text Logic Tasks
    if type == "url" and url:
        tasks.append(asyncio.to_thread(RuleEngine.analyze_url, url))
        # Domain age and risk analysis
        tasks.append(asyncio.to_thread(analyze_domain, url))
    
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
    domain_info = None
    domain_reasons = []
    scanned_domain = None

    for res in results:
        if isinstance(res, list):
            all_findings.extend(res)
        elif isinstance(res, dict):
            # General findings and metadata
            if "findings" in res:
                all_findings.extend(res["findings"])
            if "metadata" in res:
                metadata.update(res["metadata"])
            # Handle domain analysis results specifically
            if "domain" in res:
                scanned_domain = res.get("domain")
                domain_info = res.get("details") or res.get("domain_info")
                # Add domain-specific findings if not already in 'findings'
                if "reasons" in res:
                    all_findings.extend(res["reasons"])
                    domain_reasons = res["reasons"]
                elif "findings" in res and res.get("domain"):
                     domain_reasons = res["findings"]

    # --- PHASE 3: Multi-Factor Verdict ---
    score_result = ScoringService.calculate_score(all_findings)
    final_findings = score_result.get("findings", all_findings)
    recommendations = ScoringService.generate_recommendations(score_result["label"], final_findings)

    # --- PHASE 4: Company/Location/Contact Verification ---
    verification = await run_verification(
        text=extracted_text,
        url=url,
        company_name=metadata["company"],
        job_title=metadata["title"],
        location=metadata["location"]
    )

    response = ScanResponse(
        id=str(uuid.uuid4()),
        request_hash=request_hash,
        company_name=metadata["company"],
        job_title=metadata["title"],
        location=metadata["location"],
        score=score_result["score"],
        label=score_result["label"],
        score_breakdown=ScoreBreakdown(**score_result["breakdown"]) if "breakdown" in score_result else None,
        findings=[Finding(**f) for f in final_findings if isinstance(f, dict)],
        evidence=[f["message"] for f in final_findings if isinstance(f, dict) and "message" in f],
        actions=recommendations,
        createdAt=datetime.utcnow(),
        domain=scanned_domain,
        domain_info=domain_info,
        domain_reasons=domain_reasons,
        verification=verification
    )
    
    # Persistence
    if db is not None:
        try:
            # UPSERT: Replace existing result for the same content if it exists
            # This handles 'refresh=True' properly and avoids double-storing
            await db.scans.replace_one(
                {"request_hash": request_hash},
                response.dict(),
                upsert=True
            )
        except Exception as e:
            print(f"DB Update Error: {e}")
    else:
        print("Warning: Database not connected. Result not saved.")
        
    return response

@app.get("/health")
async def health(): return {"status": "healthy"}
