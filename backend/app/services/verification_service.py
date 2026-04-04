"""
Verification Service for Company/Location/Contact Verification
Extends existing platform_verifier with contact verification features
"""
import re
import httpx
import dns.resolver
import tldextract
from typing import List, Dict, Optional
from app.core.config import settings


class VerificationService:
    """Handles company, location, and contact verification"""

    # Suspicious email domains (free email services that scammers often use)
    SUSPICIOUS_EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "aol.com", "protonmail.com", "icloud.com"
    ]

    # Trusted company TLDs
    TRUSTED_TLDS = [".com", ".co.in", ".in", ".org", ".net", ".io"]

    @staticmethod
    def extract_emails_from_text(text: str) -> List[str]:
        """Extract all email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text.lower())

    @staticmethod
    def extract_domain_from_url(url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}"
            return extracted.domain
        except Exception:
            return None

    @staticmethod
    def get_domain_mx_records(domain: str) -> List[str]:
        """Get MX records for a domain"""
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            return [str(rdata).strip('.') for rdata in answers]
        except Exception:
            return []

    @staticmethod
    def analyze_contact_from_job(text: str, domain: Optional[str]) -> Dict:
        """
        Analyze contact information from job description
        Returns contact verification results
        """
        result = {
            "emails_found": [],
            "domain_mx_status": None,
            "contact_verified": False,
            "warnings": [],
            "explanation": ""
        }

        # 1. Extract emails from job description
        job_emails = VerificationService.extract_emails_from_text(text)
        result["emails_found"] = job_emails

        if not job_emails:
            result["warnings"].append("No email address found in job description")
            result["explanation"] = "No contact email provided - this is unusual for legitimate job postings"
            return result

        # 2. Analyze each email
        job_email_domain = job_emails[0].split('@')[1] if job_emails else None

        # Check if using free email service
        if job_email_domain in VerificationService.SUSPICIOUS_EMAIL_DOMAINS:
            result["warnings"].append(f"Job contact uses free email service (@{job_email_domain})")
            result["explanation"] = f"Legitimate companies use official company domains, not free email services like {job_email_domain}"

        # 3. Check domain MX records
        if job_email_domain:
            mx_records = VerificationService.get_domain_mx_records(job_email_domain)
            if mx_records:
                result["domain_mx_status"] = f"Has {len(mx_records)} mail server(s)"
            else:
                result["warnings"].append(f"Contact domain {job_email_domain} has no MX records")
                result["explanation"] = f"The email domain @{job_email_domain} cannot receive emails - highly suspicious"

        # 4. Compare with company domain if available
        if domain and job_email_domain:
            company_domain = domain.lower()
            job_domain = job_email_domain.lower()

            if company_domain == job_domain:
                result["contact_verified"] = True
                result["explanation"] = f"Contact email uses company domain (@{company_domain}) - verified"
            elif job_email_domain in VerificationService.SUSPICIOUS_EMAIL_DOMAINS:
                result["contact_verified"] = False
                # Already explained above
                pass
            else:
                result["warnings"].append(f"Contact domain ({job_email_domain}) differs from company domain ({company_domain})")
                result["explanation"] = f"Contact email uses @{job_email_domain} but company domain is {company_domain} - verify this is intentional"

        return result

    @staticmethod
    async def verify_company_official(domain: str, company_name: str) -> Dict:
        """
        Verify company official online presence
        """
        result = {
            "official_website": None,
            "careers_page": None,
            "linkedin": None,
            "glassdoor": None,
            "verified": False,
            "explanation": ""
        }

        if not domain:
            result["explanation"] = "No domain provided for verification"
            return result

        # Build URLs to check
        result["official_website"] = f"https://{domain}"

        # Try to find careers and social pages
        if not settings.SERPAPI_API_KEY:
            result["explanation"] = "SERPAPI key not configured - limited verification"
            return result

        async with httpx.AsyncClient() as client:
            query = f'"{company_name}" careers page site:{domain}'
            url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"

            try:
                response = await client.get(url)
                data = response.json()
                organic = data.get("organic_results", [])

                for res in organic[:5]:
                    link = res.get("link", "").lower()
                    title = res.get("title", "").lower()

                    if "career" in title or "career" in link:
                        result["careers_page"] = link
                    if "linkedin" in link:
                        result["linkedin"] = link
                    if "glassdoor" in link:
                        result["glassdoor"] = link

                # Determine if verified
                if result["careers_page"] or result["linkedin"]:
                    result["verified"] = True
                    result["explanation"] = "Company has official online presence (careers page/LinkedIn)"
                else:
                    result["explanation"] = "Could not find official careers page or LinkedIn"

            except Exception as e:
                result["explanation"] = f"Error during verification: {str(e)}"

        return result

    @staticmethod
    async def verify_location(input_location: str, company_name: str) -> Dict:
        """
        Verify location from job description against company known locations
        """
        result = {
            "job_location": input_location or "Not specified",
            "company_locations": [],
            "match_found": False,
            "explanation": ""
        }

        if not input_location:
            result["explanation"] = "No location provided in job description"
            return result

        # Search for company locations
        if company_name and company_name != "Unknown Company" and settings.SERPAPI_API_KEY:
            async with httpx.AsyncClient() as client:
                query = f'"{company_name}" headquarters location cities'
                url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"

                try:
                    response = await client.get(url)
                    data = response.json()
                    knowledge_graph = data.get("knowledge_graph", {})

                    # Get known locations
                    address = knowledge_graph.get("address")
                    if address:
                        result["company_locations"].append(address)

                    # Also check local results
                    for res in data.get("organic_results", [])[:5]:
                        title = res.get("title", "")
                        if any(loc in title.lower() for loc in ["india", "usa", "uk", "headquarter", "office", "city"]):
                            if title not in result["company_locations"]:
                                result["company_locations"].append(title)

                except Exception:
                    pass

        # Check for location match
        input_location_lower = input_location.lower()
        for company_loc in result["company_locations"]:
            if any(word in company_loc.lower() for word in input_location_lower.split()):
                result["match_found"] = True
                result["explanation"] = f"Job location '{input_location}' matches company location '{company_loc}'"
                break

        if not result["match_found"]:
            if result["company_locations"]:
                result["explanation"] = f"Job location '{input_location}' not found in company's known locations: {', '.join(result['company_locations'][:2])}"
            else:
                result["explanation"] = f"Job location '{input_location}' could not be verified against company locations"

        return result


async def run_verification(text: str, url: Optional[str], company_name: str, job_title: str, location: str) -> Dict:
    """
    Run all verifications and return combined results
    """
    import asyncio

    # Extract domain from URL
    domain = VerificationService.extract_domain_from_url(url) if url else None

    # Build tasks list
    tasks = []

    # Company verification
    if domain:
        tasks.append(VerificationService.verify_company_official(domain, company_name))
    else:
        async def empty_company():
            return {}
        tasks.append(empty_company())

    # Location verification
    if location:
        tasks.append(VerificationService.verify_location(location, company_name))
    else:
        async def empty_location():
            return {}
        tasks.append(empty_location())

    # Contact verification (sync but we wrap in to_thread)
    tasks.append(asyncio.to_thread(VerificationService.analyze_contact_from_job, text, domain))

    # Run all in parallel
    results = await asyncio.gather(*tasks)

    return {
        "company": results[0] if isinstance(results[0], dict) else {},
        "location": results[1] if isinstance(results[1], dict) else {},
        "contact": results[2] if isinstance(results[2], dict) else {}
    }