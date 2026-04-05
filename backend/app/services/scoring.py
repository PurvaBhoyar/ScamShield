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
    Multi-factor scoring system with justified weights.

    Deterministic Checks (Weight 40-50): Technical proofs that cannot be faked
    - Domain has no MX records = Critical (45 points)
    - Domain is not registered = Critical (50 points)
    - Domain < 30 days old = High (35 points)
    - Blacklist match = Critical (45 points)
    - Payment requested = Critical (50 points)
    - PII requested = High (40 points)

    Probabilistic Checks (Weight 10-25): Behavioral signals
    - Urgency tactics = Medium (15 points)
    - Free email domain = Medium (20 points)
    - Suspicious TLD = Medium (15 points)
    - AI-generated text = Low (10 points)
    - Vague description = Low (10 points)

    Trust Multipliers (Negative -30 to -50): Social proof
    - LinkedIn company verified = -40
    - Official careers page match = -45
    - Company has established domain (>1 year) = -30
    - Valid MX records = -25
    """

    # Category to weight type mapping
    WEIGHT_TYPES = {
        # Deterministic (technical proofs)
        "no_mx": "deterministic",
        "null_mx": "deterministic",
        "domain_not_registered": "deterministic",
        "domain_very_new": "deterministic",
        "new_domain": "deterministic",  # RuleEngine returns this
        "blacklist_match": "deterministic",
        "payment_request": "deterministic",
        "pii_request": "deterministic",
        "free_email_recruiter": "deterministic",

        # Probabilistic (behavioral signals)
        "agent_no_record": "probabilistic",
        "no_record": "probabilistic",
        "domain_young": "probabilistic",
        "young_domain": "probabilistic",
        "urgency_tactic": "probabilistic",
        "urgency": "probabilistic",  # RuleEngine returns this
        "suspicious_tld": "probabilistic",
        "suspicious_domain": "probabilistic",  # RuleEngine returns this
        "unrealistic_salary": "probabilistic",
        "no_careers_match": "probabilistic",
        "company_unverified": "probabilistic",
        "no_contact_email": "probabilistic",
        "template_match": "probabilistic",

        # Trust multipliers (reduce risk)
        "company_linkedin_verified": "trust",
        "company_glassdoor_verified": "trust",
        "careers_page_match": "trust",
        "job_board_match": "trust",
        "domain_established": "trust",
        "mx_records_found": "trust",
        "corporate_email_verified": "trust",
        "agent_verified_company": "trust",  # PlatformVerifier returns this
        "agent_verified_job": "trust",
    }

    # Weight points for each finding type
    FINDING_WEIGHTS = {
        # Deterministic (critical technical proofs)
        "no_mx": 45,
        "null_mx": 45,
        "domain_not_registered": 50,
        "domain_very_new": 35,
        "new_domain": 40,  # RuleEngine returns this - critical
        "blacklist_match": 45,
        "payment_request": 50,
        "pii_request": 40,
        "free_email_recruiter": 40,
        "unrealistic_salary": 35,

        # Probabilistic (behavioral signals)
        "agent_no_record": 15,
        "no_record": 15,
        "domain_young": 20,
        "young_domain": 15,
        "urgency_tactic": 15,
        "urgency": 15,  # RuleEngine returns this
        "suspicious_tld": 18,
        "suspicious_domain": 20,  # RuleEngine returns this
        "no_careers_match": 20,
        "company_unverified": 22,
        "no_contact_email": 12,
        "template_match": 25,

        # Trust multipliers (negative = reduce risk)
        "company_linkedin_verified": -40,
        "company_glassdoor_verified": -35,
        "careers_page_match": -45,
        "job_board_match": -30,
        "domain_established": -30,
        "mx_records_found": -25,
        "corporate_email_verified": -28,
        "agent_verified_company": -35,  # PlatformVerifier
        "agent_verified_job": -30,
    }

    # Severity adjustments within each type
    SEVERITY_ADJUSTMENTS = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.50,
        "low": 0.25,
        "safe": 0.0  # Already negative
    }

    # Thresholds (statistically derived)
    THRESHOLDS = {
        "safe": 20,     # 0-20: Low risk
        "caution": 40    # 21-40: Medium risk
    }

    @classmethod
    def calculate_score(cls, findings: List[Dict]) -> Dict:
        """
        Calculate score with UI point injection and probabilistic damping.
        """
        print(f"🎯 calculate_score called with {len(findings)} findings")

        if not findings:
            return {
                "score": 0,
                "label": "Safe",
                "findings": [],
                "breakdown": {"deterministic": 0, "probabilistic": 0, "trust_bonus": 0, "net_score": 0}
            }

        deterministic_score = 0
        probabilistic_score = 0
        trust_bonus = 0

        # Track unique findings
        seen_types = set()
        updated_findings = []

        for finding in findings:
            f_type = finding.get("type")
            severity = finding.get("severity", "medium")

            if f_type in seen_types:
                continue
            seen_types.add(f_type)

            weight_type = cls.WEIGHT_TYPES.get(f_type, "probabilistic")
            base_weight = cls.FINDING_WEIGHTS.get(f_type, 15)  # Default 15 points for unknown types

            if base_weight >= 0:
                severity_mult = cls.SEVERITY_ADJUSTMENTS.get(severity, 0.5)
                contribution = int(base_weight * severity_mult)
            else:
                contribution = base_weight # Trust multipliers are negative

            # Inject points into the finding for UI transparency
            finding_copy = finding.copy()
            finding_copy["points"] = contribution
            updated_findings.append(finding_copy)

            if weight_type == "deterministic":
                deterministic_score += contribution
            elif weight_type == "probabilistic":
                probabilistic_score += contribution
            else:  # trust
                trust_bonus += abs(contribution)

        # --- Damping Logic for Unverified Legit Companies ---
        # If no deterministic red flags (payment, PII, blacklist, etc.) are found,
        # we damp the probabilistic score so it doesn't cross 'Danger' alone.
        has_deterministic_red_flags = any(
            cls.WEIGHT_TYPES.get(f.get("type")) == "deterministic" and f.get("points", 0) > 0
            for f in updated_findings
        )

        if not has_deterministic_red_flags and probabilistic_score > 35:
            # Dampen probabilistic noise if it's the only signal
            # BUT: If probabilistic_score is very high (e.g. > 60), it's likely a scam
            # even without deterministic proofs.
            if probabilistic_score > 60:
                # Less damping for very high behavioral signals
                probabilistic_score = 45 + (probabilistic_score - 60) * 0.7
            else:
                probabilistic_score = 35 + (probabilistic_score - 35) * 0.4

        base_score = deterministic_score + probabilistic_score
        
        # Critical deterministic findings cannot be overridden by trust
        has_critical = any(
            f.get("type") in ["payment_request", "no_mx", "null_mx", "domain_not_registered", "blacklist_match"]
            for f in updated_findings
        )

        if has_critical:
            final_score = base_score
        else:
            final_score = max(0, base_score - trust_bonus)

        # Cap at 100
        final_score = min(100, int(final_score))
        label = cls._determine_label(final_score)

        return {
            "score": final_score,
            "label": label,
            "findings": updated_findings, # Return updated findings with points
            "breakdown": {
                "deterministic": int(deterministic_score),
                "probabilistic": int(probabilistic_score),
                "trust_bonus": int(trust_bonus),
                "net_score": final_score
            }
        }

    @classmethod
    def _determine_label(cls, score: float) -> str:
        """Determine label based on thresholds."""
        if score <= cls.THRESHOLDS["safe"]:
            return "Safe"
        elif score <= cls.THRESHOLDS["caution"]:
            return "Caution"
        else:
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
        else:
            if "payment_request" in types:
                actions.append("DO NOT pay any registration/processing fees.")
            if "pii_request" in types:
                actions.append("Avoid sharing Aadhar/PAN details early on.")
            if "no_mx" in types or "null_mx" in types:
                actions.append("The recruiter domain cannot receive emails; highly suspicious.")
            if "free_email_recruiter" in types:
                actions.append("Recruiter using free email - verify via official company channels.")
            if "company_unverified" in types or "no_careers_match" in types:
                actions.append("This job could not be verified on LinkedIn or official portals. Confirm via a phone call.")
            if "domain_very_new" in types:
                actions.append("Domain is very new - common for scam sites. Verify company independently.")
            if "unrealistic_salary" in types:
                actions.append("Salary is unrealistically high - typical scam lure.")
            if "template_match" in types:
                actions.append("This job matches a known scam template. Do not proceed.")
        return list(set(actions))