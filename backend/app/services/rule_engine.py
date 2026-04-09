import re
import dns.resolver
import whois
from datetime import datetime
from typing import List, Dict
import tldextract

class RuleEngine:
    SUSPICIOUS_TLDS = [".tk", ".top", ".xyz", ".click", ".win", ".bid", ".club", ".link", ".site", ".website", ".pro", ".best", ".buzz", ".icu", ".live", ".click", ".download", ".work", ".gq", ".ml", ".ga", ".cf"]

    # Expanded payment keywords (50+) - Refined with word boundaries or specific markers
    PAYMENT_KEYWORDS = [
        # Direct payment requests
        r"\bregistration fee\b", r"\bsecurity deposit\b", r"\bprocessing fee\b", r"\bonboarding fee\b",
        r"\btraining fee\b", r"\blaptop security\b", r"\brefundable deposit\b", r"\bpay to join\b",
        r"\bmembership fee\b", r"\bdocument fee\b", r"\bcourier fee\b", r"\bverification fee\b", r"\bbuy a laptop\b",
        r"\bsecurity fee\b", r"\bactivation fee\b", r"\badmin fee\b", r"\bservice charge\b", r"\bconsultation fee\b",
        r"\bplacement fee\b", r"\bbrokerage fee\b", r"\bconvenience fee\b", r"\btransaction fee\b",
        # Payment methods - Require "pay" or specific markers to avoid generic matches
        r"\bpay\s+(?:via|through|using)\b", r"\brupees\b", r"\brs\.\s*\d+", r"\bupi\b",
        r"\bgoogle pay\b", r"\bphonepe\b", r"\bpaytm\b", r"\bnet banking\b",
        r"\bbank transfer\b", r"\bneft\b", r"\brtgs\b", r"\bimps\b", r"\bwire transfer\b", r"\bwestern union\b",
        r"\bsend money\b", r"\btransfer money\b",
        # Specific amounts
        r"rs\.\s*\d+", r"inr\s*\d+", r"₹\s*\d+"
    ]

    # Expanded urgency keywords (30+)
    URGENCY_KEYWORDS = [
        r"\bapply immediately\b", r"\blimited slots\b", r"\btoday only\b", r"\burgent hiring\b",
        r"\bexpires in\b", r"\blast chance\b", r"\bact fast\b", r"\bquick reply required\b",
        r"\bhiring only for next\b", r"\bapply soon\b", r"\blimited time\b",
        r"\basap\b", r"\blast opportunity\b", r"\bdeadline today\b",
        r"\bonly few left\b", r"\bhurry up\b", r"\bdon't miss\b", r"\bdon't wait\b", r"\bimmediate joining\b",
        r"\bstart today\b", r"\bposition closing\b", r"\bfill quickly\b", r"\bfew slots left\b",
        r"\binterview tomorrow\b", r"\bselected today\b", r"\boffer expires\b",
        r"\bwithin 24 hours\b", r"\bwithin 48 hours\b", r"\blast day\b", r"\bclosing soon\b"
    ]

    # Expanded PII keywords (40+)
    PII_KEYWORDS = [
        # Government IDs
        r"\baadhaar\b", r"\badhaar\b", r"\bpan card\b", r"\bpassport copy\b", r"\bpassport number\b", r"\baadhar\b",
        r"\bdriving license\b", r"\bvoter id\b", r"\bvoter card\b", r"\bration card\b", r"\bnsr pat\b",
        # Financial info
        r"\bbank account\b", r"\bbank details\b", r"\baccount number\b", r"\bifsc code\b", r"\bupi id\b",
        r"\batm card\b", r"\batm pin\b", r"\bcvv\b", r"\bexpiry date\b", r"\bnetbanking password\b",
        r"\bbank statement\b", r"\bpassbook\b", r"\bcredit card\b", r"\bdebit card number\b",
        # Personal info - Contextual markers to avoid "age" in "message"
        r"\botp\b", r"\bone time password\b", r"\bsecurity question\b", r"\banswer the question\b",
        r"\bdate of birth\b", r"\bdob\b", r"\bbirth date\b", r"\bage\s*[:=]\s*\d+", r"\bpermanent address\b", 
        r"\bphoto id\b", r"\bselfie with id\b",
        # Contact info
        r"\bwhatsapp number\b", r"\btelegram username\b"
    ]

    # Suspicious company patterns
    COMPANY_RED_FLAGS = [
        "work from home", "wfh", "part time", "full time", "flexible hours",
        "no experience", "no experience needed", "fresher can apply", "freshers welcome",
        "no interview", "no interview required", "direct joining", "immediate joining",
        "salary upto", "salary up to", "earning potential", "unlimited earning",
        "weekly payment", "daily payment", "monthly income", "extra income"
    ]

    # Suspicious contact patterns
    CONTACT_RED_FLAGS = [
        "telegram", "whatsapp", "whats app", "message on telegram", "contact on whatsapp",
        "call now", "dial now", "join our group", "add on telegram", "add on whatsapp",
        "text us", "ping us", "reach out", "connect on", "contact via"
    ]

    @staticmethod
    def check_mx_records(domain: str) -> List[Dict]:
        findings = []
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            if len(answers) == 0:
                findings.append({"type": "null_mx", "severity": "high", "message": f"Domain {domain} has no mail servers."})
            else:
                # MX records found - add a positive finding (clean format)
                mx_hosts = [str(rdata).strip('.') for rdata in answers]
                mx_list = ", ".join(mx_hosts[:3])  # Show max 3 MX servers
                if len(mx_hosts) > 3:
                    mx_list += f" (+{len(mx_hosts) - 3} more)"
                findings.append({"type": "mx_records_found", "severity": "safe", "message": f"Domain {domain} can receive emails (MX: {mx_list})"})
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
        import re

        # Payment keywords (critical)
        for pattern in RuleEngine.PAYMENT_KEYWORDS:
            if re.search(pattern, text_lower): 
                clean_pattern = pattern.replace(r'\b', '')
                findings.append({"type": "payment_request", "severity": "critical", "message": f"Detected: '{clean_pattern}'"})

        # Urgency keywords (medium)
        for pattern in RuleEngine.URGENCY_KEYWORDS:
            if re.search(pattern, text_lower): 
                clean_pattern = pattern.replace(r'\b', '')
                findings.append({"type": "urgency", "severity": "medium", "message": f"Detected: '{clean_pattern}'"})

        # PII keywords (high)
        for pattern in RuleEngine.PII_KEYWORDS:
            if re.search(pattern, text_lower): 
                clean_pattern = pattern.replace(r'\b', '')
                findings.append({"type": "pii_request", "severity": "high", "message": f"Asks for: '{clean_pattern}'"})

        # Company red flags (suspicious job offers)
        for kw in RuleEngine.COMPANY_RED_FLAGS:
            if kw in text_lower: findings.append({"type": "suspicious_job_claim", "severity": "medium", "message": f"Suspicious claim: '{kw}'"})

        # Contact red flags (informal contact methods)
        for kw in RuleEngine.CONTACT_RED_FLAGS:
            if kw in text_lower: findings.append({"type": "informal_contact", "severity": "high", "message": f"Informal contact requested: '{kw}'"})

        # Check for unrealistic salary claims (more detailed)
        import re
        salary_patterns = [
            r"salary\s*[:=]?\s*(?:rs\.?|inr|₹)\s*(\d{2,6})",
            r"earn\s*[:=]?\s*(?:rs\.?|inr|₹)\s*(\d{2,6})",
            r"(\d{2,6})\s*(?:per|a)\s*(?:month|day|week|year)",
            r"₹\s*(\d{5,7})",  # 5+ digits after ₹
            r"(?:salary|package)\s*(?:of|up to)?\s*(?:rs\.?|inr)?\s*(\d{5,})"
        ]
        for pattern in salary_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    amount = int(match)
                    if amount > 30000:  # More than 30k/month is suspicious for most jobs
                        findings.append({
                            "type": "unrealistic_salary",
                            "severity": "high",
                            "message": f"Unrealistic salary claim: Rs. {amount}/month - typical scam lure"
                        })
                except:
                    pass

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
