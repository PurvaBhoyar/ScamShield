import asyncio
import uuid
import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.schemas.scan import ScanRequest, ScanResponse, Finding, ScoreBreakdown
from app.services.rule_engine import RuleEngine
from app.services.scoring import ScoringService
from app.services.threat_intel import ThreatIntelService
from app.services.vector_search import VectorSearchService
from app.services.ocr_service import extract_text_from_image
from app.services.ai_service import analyze_text_with_ai
from app.services.platform_verifier import PlatformVerifier

# In-memory storage for demo mode (No MongoDB needed)
IN_MEMORY_SCANS = []
MAX_RECENT_SCANS = 20

# Add missing service for URL content extraction

# Add missing service for URL content extraction
from app.services.url_service import extract_text_from_url, resolve_shortened_url
from app.services.domain_service import analyze_domain
from app.services.verification_service import run_verification
from app.services.verification_layers import EightLayerVerifier
from app.services.text_analysis_service import TextAnalysisService
from app.services.external_intel_service import run_full_external_analysis, EmailAnalyzer
from app.core.utils import generate_request_hash

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/scan", response_model=ScanResponse)
async def perform_parallel_scan(
    type: str = Form(..., pattern="^(url|text|file|audio)$"),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    refresh: bool = Form(False)
):
    # --- PHASE 0: Caching Check ---
    print(f"\n🚀 New scan request: type={type}, url={url}, text_len={len(text) if text else 0}, file={file.filename if file else None}")
    
    file_content = None
    if file:
        file_content = await file.read()
        await file.seek(0) # Reset pointer for later use
    
    request_hash = generate_request_hash(type, url, text, file_content)
    
    # Check in-memory cache
    if not refresh:
        for scan in IN_MEMORY_SCANS:
            if scan.get("request_hash") == request_hash:
                print(f"💾 In-memory cache hit: {request_hash}")
                return ScanResponse(**scan)

    all_findings = []
    extracted_text = text or ""
    audio_path = None

    # --- PHASE 1: Normalization (The Front Door) ---
    if type == "url" and url:
        # Resolve shortened URLs first
        url_resolution = await resolve_shortened_url(url)
        if url_resolution.get("is_shortened"):
            print(f"🔗 Resolved shortened URL: {url} → {url_resolution.get('resolved_url')}")
            # Add finding about shortened URL
            all_findings.append({
                "type": "shortened_url",
                "severity": "medium",
                "message": f"URL was shortened and resolved to: {url_resolution.get('resolved_url')}"
            })
            # Use resolved URL for content extraction
            url = url_resolution.get("resolved_url", url)

        # Extract content from the URL as text for secondary analysis
        url_content = await extract_text_from_url(url)
        extracted_text = f"URL Content: {url_content}\n\n{extracted_text}"

        # Also run text analysis on extracted content
        text_findings = TextAnalysisService.analyze_text(extracted_text)
        if text_findings:
            all_findings.extend(text_findings)

        # Run external threat intelligence (SSL, IP, threat feeds)
        if url:
            try:
                external_findings = await run_full_external_analysis(url, extracted_text)
                all_findings.extend(external_findings)
            except Exception as e:
                print(f"External intel error: {e}")

    elif type == "text" and text:
        # Run text analysis on direct text input
        text_findings = TextAnalysisService.analyze_text(text)
        if text_findings:
            all_findings.extend(text_findings)

    elif type == "file" and file:
        temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            # Check if it's an image or PDF for OCR
            if file.content_type.startswith("image") or file.filename.endswith(".pdf"):
                extracted_text = extract_text_from_image(temp_path)
                # Also analyze extracted text
                if extracted_text:
                    text_findings = TextAnalysisService.analyze_text(extracted_text)
                    if text_findings:
                        all_findings.extend(text_findings)
        except Exception as e:
            print(f"Extraction Error: {e}")
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
            
    # --- PHASE 2: Parallel Signal Engine (Agentic Orchestration) ---
    print(f"🔍 Input type: {type}, extracted_text length: {len(extracted_text)}")
    tasks = []
    
    # Extract domain from URL for fallback company identification
    fallback_company = None
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc:
            fallback_company = parsed.netloc.replace("www.", "").split(".")[0].capitalize()

    # Define a helper to run AI and then all Verifiers in parallel (Sequential Dependence within Parallelism)
    async def run_ai_and_verify(text: str, url: str, domain_fallback: str = None):
        findings = []
        metadata = {"company": domain_fallback or "Unknown Company", "title": "Unknown Title", "location": "Remote"}

        print(f"🤖 Running AI analysis on text: {text[:100]}...")

        # 🧠 Brain Agent: Extract entities using Groq
        ai_res = await asyncio.to_thread(analyze_text_with_ai, text)

        # print(f"🤖 AI result: {ai_res}")

        if isinstance(ai_res, dict):
            # Include soft findings from AI analysis (Urgency, Tone, etc.)
            findings.extend(ai_res.get("findings", []))

            # Use extracted metadata if valid, otherwise keep fallback
            extracted_company = ai_res.get("company_name")
            if extracted_company and extracted_company not in ["Unknown", "Unknown Company", "None"]:
                metadata["company"] = extracted_company

            extracted_title = ai_res.get("job_title")
            if extracted_title and extracted_title not in ["Unknown", "Unknown Title", "None"]:
                metadata["title"] = extracted_title

            extracted_loc = ai_res.get("location")
            if extracted_loc and extracted_loc not in ["Unknown", "Not Found", "None"]:
                metadata["location"] = extracted_loc

        # 🕵️ Professional 8-Layer Verification (only if URL provided)
        if url:
            try:
                layer_res = await EightLayerVerifier.verify_all(
                    text, url, metadata["company"], metadata["title"], metadata["location"]
                )

                if isinstance(layer_res, dict):
                    if "findings" in layer_res:
                        findings.extend(layer_res["findings"])
                    if "metadata" in layer_res:
                        m = layer_res["metadata"]
                        if m.get("location") and m["location"] != "Not Found":
                            metadata["location"] = m["location"]
            except Exception as e:
                print(f"⚠️ Verification layers error: {type(e).__name__}: {str(e)[:100]}")

        print(f"🤖 Total findings from AI+Verification: {len(findings)}")
        return {"findings": findings, "metadata": metadata}

    # 1. Forensic & Text Logic Tasks
    if type == "url" and url:
        tasks.append(asyncio.to_thread(RuleEngine.analyze_url, url))
        # Domain age and risk analysis
        tasks.append(asyncio.to_thread(analyze_domain, url))
    
    if extracted_text:
        print(f"📝 Processing text: {extracted_text[:200]}...")
        # Rule-based text analysis (Blacklist words, patterns)
        tasks.append(asyncio.to_thread(RuleEngine.analyze_text, extracted_text))
        
        # NOTE: Skipping DB-dependent lookups (ThreatIntel + VectorSearch) in demo mode
        # Agentic Research Flow - just add directly
        tasks.append(run_ai_and_verify(extracted_text, url, fallback_company))

    # --- EXECUTE ALL AGENTS IN PARALLEL ---
    results = await asyncio.gather(*tasks, return_exceptions=True)

    metadata = {"company": "Unknown", "title": "Unknown", "location": "Not Found"}
    domain_info = None
    domain_reasons = []
    scanned_domain = None

    print(f"📊 Total tasks executed: {len(results)}")
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"❌ Task {i} error: {str(res)[:100]}")
        elif isinstance(res, list):
            print(f"📋 Task {i} returned {len(res)} list items")
            all_findings.extend(res)
        elif isinstance(res, dict):
            print(f"📋 Task {i} returned dict with keys: {list(res.keys())}")
            # General findings and metadata
            if "findings" in res:
                print(f"   → findings count: {len(res['findings'])}")
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

    print(f"🔍 Total findings collected: {len(all_findings)}")
    for f in all_findings:
        print(f"   - {f.get('type', 'unknown')}: {f.get('message', '')[:50]}")

    # --- PHASE 3: Multi-Factor Verdict ---
    score_result = ScoringService.calculate_score(all_findings)
    print(f"🎯 SCORE RESULT: {score_result}")
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
        justification=score_result.get("justification", []),
        score_breakdown=ScoreBreakdown(**score_result["breakdown"]) if "breakdown" in score_result else None,
        findings=[Finding(**f) for f in final_findings if isinstance(f, dict)],
        evidence=[f["message"] for f in final_findings if isinstance(f, dict) and "message" in f],
        actions=recommendations,
        createdAt=datetime.utcnow(),
        domain=scanned_domain,
        domain_info=domain_info,
        domain_reasons=domain_reasons,
        verification=verification,
        type=type
    )
    
    # Persistence: In-memory
    IN_MEMORY_SCANS.insert(0, response.dict())
    if len(IN_MEMORY_SCANS) > MAX_RECENT_SCANS:
        IN_MEMORY_SCANS.pop()
        
    return response

@app.get("/api/scans/recent")
async def get_recent_scans(limit: int = 5):
    """Fetch the most recent scan results from memory."""
    formatted_scans = []
    for scan in IN_MEMORY_SCANS[:limit]:
        # Determine target for display
        target = scan.get("company_name") or "Unknown"
        if scan.get("domain"):
            target = scan["domain"]
        elif scan.get("job_title") and scan["job_title"] != "Unknown":
            target = f"{scan['job_title']} at {target}"
        
        formatted_scans.append({
            "id": scan.get("id"),
            "type": scan.get("type", "url"),
            "score": scan.get("score", 0),
            "label": scan.get("label", "Unknown"),
            "createdAt": scan.get("createdAt"),
            "target": target
        })
    return formatted_scans

@app.get("/health")
async def health():
    """Simple health check for demo mode."""
    return {
        "status": "healthy",
        "mode": "demo_in_memory",
        "version": "1.0.0"
    }

@app.get("/api/detection-coverage")
async def get_detection_coverage():
    """Get information about what the detection system covers."""
    from app.services.rule_engine import RuleEngine
    return {
        "detection_layers": [
            "Rule-based keyword analysis (payment, urgency, PII)",
            "AI-powered text analysis (Groq Llama 3.1)",
            "8-layer verification (company, domain, salary, etc.)",
            "External threat intelligence (OpenPhish, URLhaus, abuse.ch)",
            "SSL certificate analysis",
            "IP intelligence and geolocation",
            "Email address analysis",
            "URL shortener resolution",
            "Scam template matching (AI-driven)"
        ],
        "coverage": {
            "suspicious_tlds": len(RuleEngine.SUSPICIOUS_TLDS),
            "payment_keywords": len(RuleEngine.PAYMENT_KEYWORDS),
            "urgency_keywords": len(RuleEngine.URGENCY_KEYWORDS),
            "pii_keywords": len(RuleEngine.PII_KEYWORDS)
        },
        "features": {
            "url_scanning": True,
            "text_scanning": True,
            "file_ocr": True,
            "audio_analysis": False,
            "external_threat_feeds": True,
            "ssl_analysis": True,
            "ip_analysis": True
        }
    }
