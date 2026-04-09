"""
Scoring Service with mathematically justified weighted scoring.

Methodology (Professional Standard):
- Deterministic (Weight 40-50): Technical proofs - MX, domain age, blacklist matches
- Probabilistic (Weight 10-25): Behavioral signals - urgency, grammar, vague descriptions
- Trust Multiplier (-30 to -50): Social proof - LinkedIn verified, official careers

This creates a justifiable scoring system where:
- A single deterministic proof (e.g., no MX records) alone can trigger Danger
- Probabilistic signals need accumulation to reach Danger
- Trust signals significantly reduce risk but require no counter-indicators
"""

from typing import List, Dict
import math


class ScoringService:
    """
    Advanced Scoring Service with Correlation Damping and Compounding Risk.
    """

    # Category to weight type mapping
    WEIGHT_TYPES = {
        # Deterministic (Technical proofs)
        "no_mx": "deterministic", "null_mx": "deterministic",
        "domain_not_registered": "deterministic", "domain_very_new": "deterministic",
        "new_domain": "deterministic", "blacklist_match": "deterministic",
        "payment_request": "deterministic", "pii_request": "deterministic",
        "external_threat_match": "deterministic", "ssl_expired": "deterministic",
        "ssl_invalid": "deterministic", "ssl_hostname_mismatch": "deterministic",
        "email_typosquatting": "deterministic", "blacklisted_upi": "deterministic",
        "blacklisted_phone": "deterministic", "blacklisted_telegram": "deterministic",

        # Probabilistic (Behavioral signals)
        "urgency_tactic": "probabilistic", "urgency": "probabilistic",
        "suspicious_tld": "probabilistic", "unrealistic_salary": "probabilistic",
        "no_careers_match": "probabilistic", "company_unverified": "probabilistic",
        "template_match": "probabilistic", "ai_generated_pattern": "probabilistic",
        "shortened_url": "probabilistic", "informal_contact": "probabilistic",
        "free_email_provider": "probabilistic", "free_email_recruiter": "probabilistic",

        # Trust multipliers (Risk Reduction)
        "company_linkedin_verified": "trust", "company_glassdoor_verified": "trust",
        "careers_page_match": "trust", "domain_established": "trust",
        "mx_records_found": "trust", "corporate_email_verified": "trust",
        "ssl_valid": "trust", "ip_resolved": "trust"
    }

    # Base points for each finding
    FINDING_WEIGHTS = {
        "external_threat_match": 85, "payment_request": 75, "email_typosquatting": 70,
        "domain_not_registered": 65, "no_mx": 60, "blacklist_match": 60,
        "blacklisted_upi": 65, "blacklisted_phone": 60, "blacklisted_telegram": 60,
        "ssl_invalid": 55, "ssl_hostname_mismatch": 50, "pii_request": 50,
        "domain_very_new": 45, "free_email_recruiter": 35, "unrealistic_salary": 40,
        "template_match": 45, "informal_contact": 30, "shortened_url": 20,
        "urgency": 15, "suspicious_tld": 15, "ai_generated_pattern": 10,
        "no_careers_match": 15, "company_unverified": 15,

        # Negative values for Trust
        "careers_page_match": -60, "company_linkedin_verified": -50,
        "corporate_email_verified": -45, "domain_established": -35,
        "mx_records_found": -25, "ssl_valid": -20
    }

    @classmethod
    def calculate_score(cls, findings: List[Dict]) -> Dict:
        """
        Bayesian-style calculation with compounding risk.
        """
        if not findings:
            return {"score": 0, "label": "Safe", "findings": [], "breakdown": {}}

        base_score = 0
        trust_bonus = 0
        seen_types = set()
        updated_findings = []
        justifications = []
        
        # 1. Base Aggregation with Deduplication
        for f in findings:
            f_type = f.get("type")
            if f_type in seen_types: continue
            seen_types.add(f_type)

            weight = cls.FINDING_WEIGHTS.get(f_type, 15)
            
            # Severity mapping for weight adjustment
            severity_mult = {"critical": 1.2, "high": 1.0, "medium": 0.7, "low": 0.4, "safe": 1.0}.get(f.get("severity", "medium"), 1.0)
            
            if weight > 0:
                contribution = int(weight * severity_mult)
                base_score += contribution
            else:
                contribution = weight # trust is negative
                trust_bonus += abs(contribution)
                
            f_copy = f.copy()
            f_copy["points"] = contribution
            updated_findings.append(f_copy)

        # 2. ⚡ COMPONENT: Risk Correlation (The "Robust" Logic)
        risk_multipliers = 1.0
        
        # Cluster A: Domain Fraud
        domain_red_flags = {"domain_very_new", "no_mx", "suspicious_tld", "domain_not_registered", "email_typosquatting"}
        found_domain_flags = seen_types.intersection(domain_red_flags)
        if len(found_domain_flags) >= 2:
            risk_multipliers += (len(found_domain_flags) * 0.25)
            justifications.append(f"Compounding Risk: Multiple domain-level inconsistencies found ({len(found_domain_flags)} flags)")

        # Cluster B: Financial/PII Fraud
        intent_red_flags = {"payment_request", "pii_request", "informal_contact", "blacklisted_upi"}
        found_intent_flags = seen_types.intersection(intent_red_flags)
        if len(found_intent_flags) >= 2:
            risk_multipliers += (len(found_intent_flags) * 0.3)
            justifications.append(f"Compounding Risk: Behavioral intent patterns match known recruitment scams ({len(found_intent_flags)} flags)")

        # 3. Final Score Synthesis
        raw_score = base_score * risk_multipliers
        
        # 4. Critical Floor
        if "external_threat_match" in seen_types or "blacklisted_upi" in seen_types:
            raw_score = max(raw_score, 85)
            justifications.append("Critical Hazard: Direct match in global threat intelligence database")

        # 5. Apply Trust Offset
        critical_flags = {"external_threat_match", "blacklist_match", "blacklisted_upi", "email_typosquatting", "no_mx"}
        has_critical = any(cf in seen_types for cf in critical_flags)
        
        if has_critical:
            final_score = raw_score
        else:
            final_score = raw_score - trust_bonus

        final_score = max(0, min(100, int(final_score)))
        label = cls._determine_label(final_score)

        return {
            "score": final_score,
            "label": label,
            "findings": updated_findings,
            "breakdown": {
                "base_risk": int(base_score),
                "multiplier": round(risk_multipliers, 2),
                "trust_offset": int(trust_bonus),
                "has_critical": has_critical
            },
            "justification": justifications
        }

    @classmethod
    def _determine_label(cls, score: float) -> str:
        if score <= 20: return "Safe"
        if score <= 55: return "Caution"
        return "Danger"

    @staticmethod
    def generate_recommendations(label: str, findings: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on findings."""
        actions = []
        types = [f.get("type", "") for f in findings]

        if label == "Safe":
            actions.append("Proceed with caution, no major red flags found.")
            actions.append("Always verify job offers through official company portals.")
            if "mx_records_found" in types:
                actions.append("Domain has valid email configuration - good sign.")
            if "ssl_valid" in types:
                actions.append("Website has valid SSL certificate - good sign.")
        else:
            # Critical findings
            if "payment_request" in types:
                actions.append("DO NOT pay any registration/processing fees - legitimate employers NEVER ask for this.")
            if "pii_request" in types:
                actions.append("NEVER share Aadhaar/PAN/bank details via text/email - legitimate companies won't ask this way.")
            if "external_threat_match" in types:
                actions.append("WARNING: This URL is known to be malicious. Do not visit or share any information.")
            if "email_typosquatting" in types:
                actions.append("Email domain impersonates a real company - this is a scam.")

            # High severity
            if "no_mx" in types or "null_mx" in types:
                actions.append("The recruiter domain cannot receive emails - highly suspicious.")
            if "free_email_provider" in types or "free_email_recruiter" in types:
                actions.append("Recruiter using free email (@gmail.com, @yahoo.com) - verify via official company channels.")
            if "unrealistic_salary" in types:
                actions.append("Salary is unrealistically high - if it sounds too good to be true, it is.")
            if "suspicious_email_pattern" in types:
                actions.append("Email pattern looks suspicious (generic numbers in address).")
            if "template_match" in types:
                actions.append("This job matches a known scam template - do not proceed.")
            if "ssl_expired" in types or "ssl_invalid" in types:
                actions.append("Website has invalid/expired SSL certificate - do not trust.")
            if "dns_resolution_failed" in types:
                actions.append("Domain cannot be resolved - may be offline or fake.")

            # Medium severity
            if "informal_contact" in types or "informal_contact_request" in types:
                actions.append("Contact via WhatsApp/Telegram is unprofessional - legitimate employers use official email.")
            if "urgency" in types or "urgency_tactic" in types:
                actions.append("Urgency tactics are common in scams - take time to verify.")
            if "suspicious_job_claim" in types:
                claims = [f for f in findings if f.get("type") == "suspicious_job_claim"]
                if claims:
                    actions.append(f"Check claim: {claims[0].get('message', '')}")
            if "company_unverified" in types or "no_cares_match" in types:
                actions.append("Job not found on LinkedIn or company careers page - verify by calling company directly.")
            if "domain_very_new" in types:
                actions.append("Domain is very new (<90 days) - common for scam sites.")

            # General advice
            actions.append("When in doubt, call the company directly using their official number (not one provided in the job).")
            actions.append("Search for the company on LinkedIn to verify they exist and are hiring.")
        return list(set(actions))