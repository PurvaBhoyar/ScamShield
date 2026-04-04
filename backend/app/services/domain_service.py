import whois
from datetime import datetime
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
import tldextract


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return extracted.domain or None
    except Exception:
        return None


def get_domain_info(domain: str) -> Dict[str, Any]:
    """
    Get domain information using WHOIS lookup.
    """
    try:
        w = whois.whois(domain)
        if not w:
            return {
                "registered": False,
                "domain_name": domain,
                "registrar": None,
                "creation_date": None,
                "expiration_date": None,
                "age_days": None,
                "registrar_country": None,
            }

        creation_date = w.creation_date
        expiration_date = w.expiration_date

        # Handle list of dates (some WHOIS responses return lists)
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]

        # Calculate age in days
        age_days = None
        if creation_date:
            if isinstance(creation_date, str):
                try:
                    creation_date = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        creation_date = datetime.strptime(creation_date, "%Y-%m-%d")
                    except:
                        creation_date = None

            if creation_date and isinstance(creation_date, datetime):
                age_days = (datetime.now() - creation_date).days

        # Get registrar info
        registrar = w.registrar
        if isinstance(registrar, list):
            registrar = registrar[0] if registrar else None

        # Get registrar country
        registrar_country = None
        if w.registrar:
            if hasattr(w.registrar, 'get'):
                registrar_country = w.registrar.get('country')

        return {
            "registered": True,
            "domain_name": domain,
            "registrar": registrar,
            "creation_date": str(creation_date) if creation_date else None,
            "expiration_date": str(expiration_date) if expiration_date else None,
            "age_days": age_days,
            "registrar_country": registrar_country,
            "name_servers": w.name_servers if hasattr(w, 'name_servers') else None,
            "status": w.status if hasattr(w, 'status') else None,
        }
    except Exception as e:
        print(f"WHOIS lookup error for {domain}: {e}")
        return {
            "registered": False,
            "domain_name": domain,
            "registrar": None,
            "creation_date": None,
            "expiration_date": None,
            "age_days": None,
            "registrar_country": None,
            "error": str(e)
        }


def calculate_domain_risk(domain_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate risk score based on domain information.
    """
    score = 0
    reasons: List[Dict[str, str]] = []

    # Check if domain is registered
    if not domain_info.get("registered"):
        score += 50
        reasons.append({
            "type": "domain_not_registered",
            "severity": "high",
            "message": "Domain not registered - could be newly created for scam"
        })
        return {
            "score": score,
            "reasons": reasons,
            "details": domain_info
        }

    age = domain_info.get("age_days")

    if age is not None:
        if age < 30:
            score += 40
            reasons.append({
                "type": "domain_very_new",
                "severity": "high",
                "message": f"Domain is very new ({age} days old) - common for scam sites"
            })
        elif age < 90:
            score += 20
            reasons.append({
                "type": "domain_new",
                "severity": "medium",
                "message": f"Domain is relatively new ({age} days old)"
            })
        elif age < 180:
            score += 10
            reasons.append({
                "type": "domain_moderate_age",
                "severity": "low",
                "message": f"Domain age is {age} days"
            })
        else:
            reasons.append({
                "type": "domain_established",
                "severity": "safe",
                "message": f"Domain is established ({age} days old)"
            })

    # Check registrar info
    if not domain_info.get("registrar"):
        score += 10
        reasons.append({
            "type": "missing_registrar",
            "severity": "medium",
            "message": "Missing registrar information"
        })

    # Check for suspicious registrar countries
    suspicious_registrars = ['CN', 'RU', 'KZ', 'BY', 'UA', 'KP']
    registrar_country = domain_info.get("registrar_country")
    if registrar_country in suspicious_registrars:
        score += 15
        reasons.append({
            "type": "suspicious_registrar_country",
            "severity": "medium",
            "message": f"Registrar located in {registrar_country} (high-risk country)"
        })

    # Check for free/low-cost registrars often used by scammers
    free_registrars = ['freenom', 'godaddy', 'namecheap', 'enom', 'godaddy']
    registrar = domain_info.get("registrar", "").lower() if domain_info.get("registrar") else ""
    if any(r in registrar for r in free_registrars):
        reasons.append({
            "type": "budget_registrar",
            "severity": "low",
            "message": "Domain registered with budget registrar (common for personal/scam sites)"
        })

    return {
        "score": min(score, 100),  # Cap at 100
        "reasons": reasons,
        "details": domain_info
    }


def analyze_domain(url: str) -> Dict[str, Any]:
    """
    Full domain analysis - extract domain, get WHOIS info, calculate risk.
    """
    domain = extract_domain_from_url(url)
    if not domain:
        return {
            "error": "Could not extract domain from URL",
            "risk_score": 0,
            "reasons": []
        }

    domain_info = get_domain_info(domain)
    risk_analysis = calculate_domain_risk(domain_info)

    return {
        "domain": domain,
        "domain_info": domain_info,
        "risk_score": risk_analysis["score"],
        "reasons": risk_analysis["reasons"],
        "details": risk_analysis["details"]
    }