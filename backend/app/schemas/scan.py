from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Finding(BaseModel):
    type: str
    severity: str
    message: str
    # Evidence-first fields
    source_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    layer: Optional[str] = None
    points: Optional[int] = 0

class Action(BaseModel):
    action: str
    status: str
    reason: str

class ScanRequest(BaseModel):
    type: str = Field(..., pattern="^(url|text|file|audio)$")
    url: Optional[str] = None
    text: Optional[str] = None
    extractedText: Optional[str] = None

class ScoreBreakdown(BaseModel):
    """Detailed breakdown of the scoring for UI transparency"""
    base_risk: int
    multiplier: float
    trust_offset: int
    has_critical: bool

class ScanResponse(BaseModel):
    id: str
    request_hash: Optional[str] = None
    company_name: Optional[str] = "Unknown"
    job_title: Optional[str] = "Unknown"
    location: Optional[str] = "Not Found"
    score: int
    label: str
    justification: Optional[List[str]] = []
    # Score breakdown for UI transparency
    score_breakdown: Optional[ScoreBreakdown] = None
    findings: List[Finding]
    evidence: List[str]
    actions: List[str]
    policyLog: Optional[List[Action]] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    # Domain analysis fields
    domain: Optional[str] = None
    domain_info: Optional[dict] = None
    domain_reasons: Optional[List[dict]] = None
    # Verification fields
    verification: Optional[dict] = None

class ScanHistory(BaseModel):
    id: str
    inputType: str
    scannedDomain: Optional[str]
    companyName: Optional[str]
    recruiterEmail: Optional[str]
    score: int
    label: str
    findings: List[str]
    createdAt: datetime
