from typing import List, Dict

class ScoringService:
    WEIGHTS = {"critical": 40, "high": 25, "medium": 15, "low": 5, "safe": -15}

    @staticmethod
    def calculate_score(findings: List[Dict]) -> Dict:
        total_risk = 0
        seen_types = set()

        # Check for trust indicators first
        has_company_verified = any(f.get("type") == "agent_verified_company" for f in findings)
        has_domain_established = any(f.get("type") == "domain_established" for f in findings)
        has_location = any(f.get("type") == "company_location_found" for f in findings)

        for finding in findings:
            severity = finding.get("severity", "low")
            f_type = finding.get("type")

            # Skip no_mx if company is verified AND domain is established
            # Large companies may use different domains for email
            if f_type in ("no_mx", "null_mx") and has_company_verified and has_domain_established:
                continue  # Skip this finding - it's a false positive for established companies

            if f_type not in seen_types:
                weight = ScoringService.WEIGHTS.get(severity, 5)
                total_risk += weight
                seen_types.add(f_type)

        # Risk cannot be negative, but trust bonus can lower risk
        final_score = max(0, min(total_risk, 100))

        # New "Hardened" thresholds:
        # Safe (< 15): No red flags found or major trust bonus verified.
        # Caution (15 - 40): Soft signals or single high-risk operational anomaly.
        # Danger (> 40): Critical scam intent (fee, blacklist) or multiple high anomalies.
        if final_score < 15:
            label = "Safe"
        elif final_score <= 40:
            label = "Caution"
        else:
            label = "Danger"

        return {"score": final_score, "label": label}

    @staticmethod
    def generate_recommendations(label: str, findings: List[Dict]) -> List[str]:
        actions = []
        types = [f["type"] for f in findings]

        if label == "Safe":
            actions.append("Proceed with caution, no major red flags found.")
            actions.append("Always verify job offers through official company portals.")
            if "mx_records_found" in types:
                actions.append("Domain has valid email configuration - good sign.")
        else:
            if "payment_request" in types: actions.append("DO NOT pay any registration/processing fees.")
            if "pii_request" in types: actions.append("Avoid sharing Aadhar/PAN details early on.")
            if "no_mx" in types or "null_mx" in types: actions.append("The recruiter domain cannot receive emails; highly suspicious.")
            if "mx_records_found" in types: actions.append("Domain has valid email configuration.")
            if "agent_no_record" in types: actions.append("This job could not be verified on LinkedIn or official portals. Confirm via a phone call.")
            if "no_official_listing" in types: actions.append("The job listing was not found on the company's official website. Please reach out to their HR directly.")
            if "company_location_missing" in types: actions.append("Could not find a physical office for this company. Verify its legal registration.")
            if "template_match" in types: actions.append("This job matches a known scam template. Do not proceed.")
        return list(set(actions))
