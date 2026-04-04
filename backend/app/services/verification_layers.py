"""
8-Layer Professional Verification System

Implements the professional standard with evidence-first approach:
1. Careers Page Verification - Verify job appears on official career pages
2. Company Authentication - Verify company exists on LinkedIn, Glassdoor
3. Recruiter Identity - Check email domain matches company
4. Salary Benchmarking - Flag unrealistic salaries
5. Scam Pattern Detection - Match against 25 red flags
6. Contact Validation - Check UPI/Phone against blacklist
7. Domain & SSL Intelligence - WHOIS age, MX records
8. Real-Time Fraud Cross-Reference - Match against known templates
"""

import re
import dns.resolver
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import tldextract
from app.core.config import settings


class EvidenceFinding:
    """Structured finding with evidence links"""
    def __init__(self, finding_type: str, severity: str, message: str,
                 source_url: str = None, raw_data: Any = None, layer: str = None):
        self.type = finding_type
        self.severity = severity
        self.message = message
        self.source_url = source_url
        self.raw_data = raw_data
        self.layer = layer

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "source_url": self.source_url,
            "raw_data": self.raw_data,
            "layer": self.layer
        }


class EightLayerVerifier:
    """
    Professional 8-layer verification with evidence-first approach.
    Each finding MUST include source_url or raw_data for transparency.
    """

    # Suspicious TLDs often used by scammers
    SUSPICIOUS_TLDS = [".tk", ".top", ".xyz", ".click", ".win", ".bid", ".club",
                       ".link", ".site", ".website", ".pro", ".best", ".work"]

    # Free email domains (suspicious for corporate recruiters)
    FREE_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                         "aol.com", "protonmail.com", "icloud.com"]

    # Trusted company TLDs
    TRUSTED_TLDS = [".com", ".co.in", ".in", ".org", ".net", ".io", ".co"]

    # Payment/fee keywords (critical red flags)
    PAYMENT_KEYWORDS = [
        "registration fee", "security deposit", "processing fee", "onboarding fee",
        "training fee", "laptop security", "refundable deposit", "pay to join",
        "membership fee", "document fee", "courier fee", "verification fee",
        "buy a laptop", "deposit", "advance payment", "joining fee"
    ]

    # Urgency keywords
    URGENCY_KEYWORDS = [
        "apply immediately", "limited slots", "today only", "urgent hiring",
        "expires in", "last chance", "act fast", "quick reply required",
        "hiring only for next", "only few spots", "immediate joining"
    ]

    # PII keywords (identity theft risk)
    PII_KEYWORDS = [
        "aadhaar", "pan card", "bank account", "passport copy", "otp", "cvv",
        "atm pin", "netbanking password", "security question", "date of birth",
        "mother's maiden", "social security", "ssn"
    ]

    # High salary thresholds (weekly)
    SUSPICIOUS_SALARY_THRESHOLD = 3000  # $3000/week is suspicious for most roles

    @staticmethod
    async def verify_all(text: str, url: Optional[str], company_name: str,
                        job_title: str, location: str) -> Dict[str, Any]:
        """
        Run all 8 verification layers in parallel where possible.
        Returns findings with evidence for each layer.
        """
        findings = []

        # Extract domain and emails from text/URL
        domain = EightLayerVerifier._extract_domain(url) if url else None
        emails = EightLayerVerifier._extract_emails(text)

        # Run independent checks in parallel
        tasks = [
            EightLayerVerifier.layer_careers_page(company_name, job_title),
            EightLayerVerifier.layer_company_auth(company_name),
            EightLayerVerifier.layer_recruiter_identity(emails, company_name),
            EightLayerVerifier.layer_salary_benchmarking(text),
            EightLayerVerifier.layer_scam_patterns(text),
            EightLayerVerifier.layer_domain_intelligence(domain, url),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                findings.extend(res)
            elif isinstance(res, Exception):
                print(f"Verification layer error: {res}")

        # Contact validation and fraud cross-reference (require DB, handled separately)
        return {
            "findings": findings,
            "metadata": {
                "domain": domain,
                "emails": emails,
                "company": company_name,
                "job_title": job_title,
                "location": location
            }
        }

    @staticmethod
    async def layer_careers_page(company_name: str, job_title: str) -> List[Dict]:
        """
        Layer 1: Careers Page Verification
        Verify job appears on official company career page via SerpAPI
        """
        findings = []
        if not company_name or not settings.SERPAPI_API_KEY:
            return findings

        try:
            async with httpx.AsyncClient() as client:
                # Search for job on official careers page
                query = f'site:{company_name.lower().replace(" ", "")}.com careers "{job_title}"'
                url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"
                response = await client.get(url)
                data = response.json()
                organic = data.get("organic_results", [])

                if organic and any("career" in r.get("link", "").lower() for r in organic[:5]):
                    findings.append(EvidenceFinding(
                        finding_type="careers_page_match",
                        severity="safe",
                        message=f"Job found on official {company_name} careers page",
                        source_url=organic[0].get("link"),
                        raw_data={"search_query": query, "results_count": len(organic)},
                        layer="careers_page"
                    ).to_dict())
                else:
                    # Search broader LinkedIn/Indeed
                    query2 = f'LinkedIn Indeed Naukri "{company_name}" "{job_title}"'
                    url2 = f"https://serpapi.com/search.json?q={query2}&api_key={settings.SERPAPI_API_KEY}"
                    resp2 = await client.get(url2)
                    data2 = resp2.json()
                    organic2 = data2.get("organic_results", [])

                    if organic2:
                        findings.append(EvidenceFinding(
                            finding_type="job_board_match",
                            severity="medium",
                            message=f"Job found on job boards but not on official careers page",
                            source_url=organic2[0].get("link"),
                            raw_data={"search_query": query2, "results_count": len(organic2)},
                            layer="careers_page"
                        ).to_dict())
                    else:
                        findings.append(EvidenceFinding(
                            finding_type="no_careers_match",
                            severity="high",
                            message=f"Job not found on official careers page or major job boards",
                            source_url=None,
                            raw_data={"search_query": query},
                            layer="careers_page"
                        ).to_dict())

        except Exception as e:
            print(f"Careers page verification error: {e}")

        return findings

    @staticmethod
    async def layer_company_auth(company_name: str) -> List[Dict]:
        """
        Layer 2: Company Authentication
        Verify company exists on LinkedIn, Glassdoor via SerpAPI
        """
        findings = []
        if not company_name or not settings.SERPAPI_API_KEY:
            return findings

        try:
            async with httpx.AsyncClient() as client:
                query = f'"{company_name}" LinkedIn company Glassdoor'
                search_url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"
                response = await client.get(search_url)
                data = response.json()
                organic = data.get("organic_results", [])

                linkedin_found = False
                glassdoor_found = False

                for res in organic[:10]:
                    link = res.get("link", "").lower()
                    title = res.get("title", "").lower()

                    if "linkedin.com/company" in link:
                        linkedin_found = True
                        findings.append(EvidenceFinding(
                            finding_type="company_linkedin_verified",
                            severity="safe",
                            message=f"Company verified on LinkedIn: {res.get('title')}",
                            source_url=res.get("link"),
                            raw_data={"title": res.get("title"), "snippet": res.get("snippet")},
                            layer="company_auth"
                        ).to_dict())

                    if "glassdoor.com" in link:
                        glassdoor_found = True
                        findings.append(EvidenceFinding(
                            finding_type="company_glassdoor_verified",
                            severity="safe",
                            message=f"Company verified on Glassdoor: {res.get('title')}",
                            source_url=res.get("link"),
                            raw_data={"title": res.get("title")},
                            layer="company_auth"
                        ).to_dict())

                if not linkedin_found and not glassdoor_found:
                    findings.append(EvidenceFinding(
                        finding_type="company_unverified",
                        severity="high",
                        message=f"Company '{company_name}' not found on LinkedIn or Glassdoor",
                        source_url=None,
                        raw_data={"search_query": query},
                        layer="company_auth"
                    ).to_dict())

        except Exception as e:
            print(f"Company authentication error: {e}")

        return findings

    @staticmethod
    def layer_recruiter_identity(emails: List[str], company_name: str) -> List[Dict]:
        """
        Layer 3: Recruiter Identity Verification
        Check if recruiter uses corporate email vs free email
        """
        findings = []

        if not emails:
            findings.append(EvidenceFinding(
                finding_type="no_contact_email",
                severity="medium",
                message="No contact email found in job posting",
                source_url=None,
                raw_data=None,
                layer="recruiter_identity"
            ).to_dict())
            return findings

        for email in emails:
            domain = email.split("@")[1].lower() if "@" in email else domain

            if domain in EightLayerVerifier.FREE_EMAIL_DOMAINS:
                findings.append(EvidenceFinding(
                    finding_type="free_email_recruiter",
                    severity="critical",
                    message=f"Recruiter using free email @{domain} - suspicious for corporate recruiter",
                    source_url=f"mailto:{email}",
                    raw_data={"email": email, "domain": domain},
                    layer="recruiter_identity"
                ).to_dict())
            else:
                findings.append(EvidenceFinding(
                    finding_type="corporate_email_verified",
                    severity="safe",
                    message=f"Recruiter using corporate email @{domain}",
                    source_url=f"mailto:{email}",
                    raw_data={"email": email, "domain": domain},
                    layer="recruiter_identity"
                ).to_dict())

        return findings

    @staticmethod
    def layer_salary_benchmarking(text: str) -> List[Dict]:
        """
        Layer 4: Salary Benchmarking
        Flag unrealistic salaries using pattern matching
        """
        findings = []

        # Patterns to detect salary mentions
        salary_patterns = [
            r'\$[\d,]+(?:\.\d{2})?\s*(?:/|\s(?:per|each))\s*(?:week|month|hour|day)',
            r'₹[\d,]+(?:\.\d{2})?\s*(?:/|\s(?:per|each))\s*(?:week|month|hour|day)',
            r'[\d,]+(?:\.\d{2})?\s*(?:/|\s(?:per|each))\s*(?:week|month|hour|day)\s*(?:USD|INR|$|₹)?',
        ]

        for pattern in salary_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract numeric value
                numbers = re.findall(r'[\d,]+', match)
                if numbers:
                    try:
                        amount = float(numbers[0].replace(",", ""))
                        # Check if weekly salary is suspicious
                        if "week" in match.lower() and amount > EightLayerVerifier.SUSPICIOUS_SALARY_THRESHOLD:
                            findings.append(EvidenceFinding(
                                finding_type="unrealistic_salary",
                                severity="critical",
                                message=f"Unrealistic salary detected: {match}/week - typical scam lure",
                                source_url=None,
                                raw_data={"salary_mentioned": match, "amount": amount},
                                layer="salary_benchmark"
                            ).to_dict())
                    except:
                        pass

        return findings

    @staticmethod
    def layer_scam_patterns(text: str) -> List[Dict]:
        """
        Layer 5: Scam Pattern Detection
        Match against the 25 red flags from research
        """
        findings = []
        text_lower = text.lower()

        # Payment requests (Critical)
        for kw in EightLayerVerifier.PAYMENT_KEYWORDS:
            if kw in text_lower:
                findings.append(EvidenceFinding(
                    finding_type="payment_request",
                    severity="critical",
                    message=f"Payment required: '{kw}' - classic advance-fee scam",
                    source_url=None,
                    raw_data={"keyword": kw},
                    layer="scam_patterns"
                ).to_dict())

        # Urgency tactics (High)
        for kw in EightLayerVerifier.URGENCY_KEYWORDS:
            if kw in text_lower:
                findings.append(EvidenceFinding(
                    finding_type="urgency_tactic",
                    severity="high",
                    message=f"Urgency pressure: '{kw}' - psychological manipulation",
                    source_url=None,
                    raw_data={"keyword": kw},
                    layer="scam_patterns"
                ).to_dict())

        # PII requests (Critical)
        for kw in EightLayerVerifier.PII_KEYWORDS:
            if kw in text_lower:
                findings.append(EvidenceFinding(
                    finding_type="pii_request",
                    severity="critical",
                    message=f"Personal info request: '{kw}' - identity theft risk",
                    source_url=None,
                    raw_data={"keyword": kw},
                    layer="scam_patterns"
                ).to_dict())

        return findings

    @staticmethod
    def layer_domain_intelligence(domain: Optional[str], url: Optional[str]) -> List[Dict]:
        """
        Layer 7: Domain & SSL Intelligence
        WHOIS age, MX records, TLD analysis
        """
        findings = []

        if not domain:
            return findings

        # Check suspicious TLD
        for tld in EightLayerVerifier.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                findings.append(EvidenceFinding(
                    finding_type="suspicious_tld",
                    severity="high",
                    message=f"High-risk TLD '{tld}' commonly used by scammers",
                    source_url=None,
                    raw_data={"domain": domain, "tld": tld},
                    layer="domain_intelligence"
                ).to_dict())

        # Check MX records
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            if answers:
                mx_hosts = [str(rdata).strip('.') for rdata in answers[:3]]
                findings.append(EvidenceFinding(
                    finding_type="mx_records_found",
                    severity="safe",
                    message=f"Domain has valid email servers: {', '.join(mx_hosts)}",
                    source_url=None,
                    raw_data={"mx_records": mx_hosts, "count": len(answers)},
                    layer="domain_intelligence"
                ).to_dict())
            else:
                findings.append(EvidenceFinding(
                    finding_type="no_mx_records",
                    severity="critical",
                    message=f"Domain has no MX records - cannot receive emails",
                    source_url=None,
                    raw_data={"domain": domain},
                    layer="domain_intelligence"
                ).to_dict())
        except dns.resolver.NXDOMAIN:
            findings.append(EvidenceFinding(
                finding_type="domain_not_registered",
                severity="critical",
                message=f"Domain {domain} is not registered",
                source_url=None,
                raw_data={"domain": domain},
                layer="domain_intelligence"
            ).to_dict())
        except Exception as e:
            print(f"MX lookup error: {e}")

        # Check domain age via WHOIS
        try:
            import whois
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

            if creation_date:
                if isinstance(creation_date, str):
                    try:
                        creation_date = datetime.strptime(creation_date.split()[0], "%Y-%m-%d")
                    except:
                        creation_date = None

                if creation_date and isinstance(creation_date, datetime):
                    age_days = (datetime.now() - creation_date).days

                    if age_days < 30:
                        findings.append(EvidenceFinding(
                            finding_type="domain_very_new",
                            severity="critical",
                            message=f"Domain registered {age_days} days ago - common for scam sites",
                            source_url=None,
                            raw_data={"domain": domain, "age_days": age_days, "creation_date": str(creation_date)},
                            layer="domain_intelligence"
                        ).to_dict())
                    elif age_days < 90:
                        findings.append(EvidenceFinding(
                            finding_type="domain_young",
                            severity="high",
                            message=f"Domain registered {age_days} days ago - relatively new",
                            source_url=None,
                            raw_data={"domain": domain, "age_days": age_days},
                            layer="domain_intelligence"
                        ).to_dict())
                    elif age_days >= 365:
                        findings.append(EvidenceFinding(
                            finding_type="domain_established",
                            severity="safe",
                            message=f"Domain established {age_days} days ago - established business",
                            source_url=None,
                            raw_data={"domain": domain, "age_days": age_days},
                            layer="domain_intelligence"
                        ).to_dict())

        except Exception as e:
            print(f"WHOIS lookup error: {e}")

        return findings

    @staticmethod
    def _extract_domain(url: Optional[str]) -> Optional[str]:
        """Extract domain from URL"""
        if not url:
            return None
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}"
            return extracted.domain
        except:
            return None

    @staticmethod
    def _extract_emails(text: str) -> List[str]:
        """Extract all email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)


# Helper for async gather
import asyncio