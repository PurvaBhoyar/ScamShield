import re
import dns.resolver
import whois
from datetime import datetime
from typing import List, Dict
import tldextract

class RuleEngine:
    SUSPICIOUS_TLDS = [".tk", ".top", ".xyz", ".click", ".win", ".bid", ".club", ".link", ".site", ".website", ".pro", ".best"]
    PAYMENT_KEYWORDS = [
        "registration fee", "security deposit", "processing fee", "onboarding fee", 
        "training fee", "laptop security", "refundable deposit", "pay to join",
        "membership fee", "document fee", "courier fee", "verification fee", "buy a laptop"
    ]
    URGENCY_KEYWORDS = [
        "apply immediately", "limited slots", "today only", "urgent hiring", 
        "expires in", "last chance", "act fast", "quick reply required",
        "hiring only for next 2 hours"
    ]
    PII_KEYWORDS = [
        "aadhaar", "pan card", "bank account", "passport copy", "otp", "cvv", 
        "atm pin", "netbanking password", "security question answer"
    ]

    @staticmethod
    def check_mx_records(domain: str) -> List[Dict]:
        findings = []
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            if len(answers) == 0:
                findings.append({"type": "null_mx", "severity": "high", "message": f"Domain {domain} has no mail servers."})
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            findings.append({"type": "no_mx", "severity": "critical", "message": f"Domain {domain} is not configured to receive email."})
        except Exception as e:
            print(f"DNS Resolution Error: {e}")
        return findings

    @staticmethod
    def get_domain_age(domain: str) -> List[Dict]:
        findings = []
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list): creation_date = creation_date[0]
            if creation_date:
                age_days = (datetime.now() - creation_date).days
                if age_days < 30:
                    findings.append({"type": "new_domain", "severity": "critical", "message": f"Domain is only {age_days} days old."})
                elif age_days < 90:
                    findings.append({"type": "young_domain", "severity": "medium", "message": f"Domain registered {age_days} days ago."})
        except Exception: pass
        return findings

    @staticmethod
    def analyze_text(text: str) -> List[Dict]:
        findings = []
        text_lower = text.lower()
        for kw in RuleEngine.PAYMENT_KEYWORDS:
            if kw in text_lower: findings.append({"type": "payment_request", "severity": "critical", "message": f"Detected: '{kw}'"})
        for kw in RuleEngine.URGENCY_KEYWORDS:
            if kw in text_lower: findings.append({"type": "urgency", "severity": "medium", "message": f"Detected: '{kw}'"})
        for kw in RuleEngine.PII_KEYWORDS:
            if kw in text_lower: findings.append({"type": "pii_request", "severity": "high", "message": f"Asks for: '{kw}'"})
        return findings

    @staticmethod
    def analyze_url(url: str) -> List[Dict]:
        findings = []
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"
        findings.extend(RuleEngine.check_mx_records(domain))
        findings.extend(RuleEngine.get_domain_age(domain))
        for tld in RuleEngine.SUSPICIOUS_TLDS:
            if domain.endswith(tld): findings.append({"type": "suspicious_domain", "severity": "high", "message": f"High-risk TLD: '{tld}'"})
        return findings
