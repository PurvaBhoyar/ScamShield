from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Finding(BaseModel):
    type: str
    severity: str
    message: str

class Action(BaseModel):
    action: str
    status: str
    reason: str

class ScanRequest(BaseModel):
    type: str = Field(..., pattern="^(url|text|file|audio)$")
    url: Optional[str] = None
    text: Optional[str] = None
    extractedText: Optional[str] = None

class ScanResponse(BaseModel):
    id: str
    company_name: Optional[str] = "Unknown"
    job_title: Optional[str] = "Unknown"
    location: Optional[str] = "Not Found"
    score: int
    label: str
    findings: List[Finding]
    evidence: List[str]
    actions: List[str]
    policyLog: Optional[List[Action]] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    # Domain analysis fields
    domain: Optional[str] = None
    domain_info: Optional[dict] = None
    domain_reasons: Optional[List[dict]] = None

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
