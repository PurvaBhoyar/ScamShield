import httpx
from urllib.parse import quote_plus
from app.core.config import settings
from typing import List, Dict

class PlatformVerifier:
    TRUSTED_PLATFORMS = [
        "linkedin.com", "internshala.com", "glassdoor.com", "razorpay.com", 
        "google.com", "amazon.com", "microsoft.com", "apple.com", "flipkart.com", 
        "zomato.com", "swiggy.com", "tata.com", "reliance.com", "infosys.com", "wipro.com",
        "facebook.com", "twitter.com", "instagram.com", "github.com"
    ]

    @staticmethod
    def _sanitize(text: str) -> str:
        """Removes non-printable ASCII or illegal URL characters."""
        if not text: return ""
        # Remove any character that isn't printable ASCII for URL safety
        return "".join(char for char in text if 32 <= ord(char) <= 126)

    @staticmethod
    def _get_api_key() -> str:
        """Strips non-printable characters from SerpAPI key."""
        key = getattr(settings, "SERPAPI_API_KEY", "")
        if not key: return ""
        return "".join(char for char in key if 32 <= ord(char) <= 126).strip()

    @staticmethod
    async def verify_job_publicly(company_name: str, job_title: str) -> List[Dict]:
        """
        Uses SerpAPI to search for the job listing on official career pages and LinkedIn.
        If found, it returns a 'Trust Bonus' (negative points).
        If not found, it flags a warning.
        """
        findings = []
        api_key = PlatformVerifier._get_api_key()
        
        # Sanitize inputs
        company_name = PlatformVerifier._sanitize(company_name)
        job_title = PlatformVerifier._sanitize(job_title)
        
        # Check if it's a known trusted company first to avoid false positives
        is_trusted = any(trusted.lower() in company_name.lower() for trusted in PlatformVerifier.TRUSTED_PLATFORMS)
        if is_trusted:
            findings.append({
                "type": "agent_verified_company",
                "severity": "safe",
                "message": f"Trust Factor: {company_name} is a recognized trusted enterprise."
            })

        if not company_name or company_name.lower() == "unknown company" or not api_key:
            # If the name is unknown and no trusted URL was found, we flag it.
            # But we lower severity to medium to avoid false positives on sparse text.
            findings.append({
                "type": "agent_no_record",
                "severity": "medium", 
                "message": f"Warning: Could not identify a clear company name for verification."
            })
            return findings
            
        async with httpx.AsyncClient() as client:
            # 🔍 Query 1: LinkedIn/Job Boards for specific Job
            # Added more job boards for broader reach
            query_job = quote_plus(f'LinkedIn Internshala Glassdoor Naukri Indeed "{company_name}" "{job_title}"')
            url_job = f"https://serpapi.com/search.json?q={query_job}&api_key={api_key}"
            
            # 🔍 Query 2: Company Presence (LinkedIn, Social Media, About)
            query_company = quote_plus(f'"{company_name}" official website LinkedIn profile Twitter Instagram About Us')
            url_company = f"https://serpapi.com/search.json?q={query_company}&api_key={api_key}"

            try:
                import asyncio
                # Run searches in parallel
                resp_job, resp_company = await asyncio.gather(
                    client.get(url_job),
                    client.get(url_company)
                )
                
                data_job = resp_job.json()
                data_company = resp_company.json()
                
                organic_job = data_job.get("organic_results", [])
                organic_company = data_company.get("organic_results", [])
                
                # 1. Check for job listing match
                found_on_platform = False
                for res in organic_job[:10]: # Check more results
                    link = res.get("link", "").lower()
                    if any(p in link for p in ["linkedin.com/jobs", "internshala.com", "glassdoor.com", "naukri.com", "indeed.com", "career"]):
                        found_on_platform = True
                        break
                
                # 2. Check for company existence
                found_company = False
                # If it's already on the trust list, we skip this check or count it as found.
                if is_trusted:
                    found_company = True
                else:
                    for res in organic_company[:10]:
                        link = res.get("link", "").lower()
                        if any(p in link for p in ["linkedin.com/company", "twitter.com", "instagram.com", "facebook.com", "careers", "about", "contact"]):
                            found_company = True
                            break

                if found_on_platform:
                    findings.append({
                        "type": "agent_verified_job",
                        "severity": "safe",
                        "message": f"Verified: Confirmed job listing for '{job_title}' at {company_name} on a reputable career platform (LinkedIn/Internshala)."
                    })
                elif found_company:
                    # If company exists but specific job title doesn't, it's safe but cautious
                    findings.append({
                        "type": "agent_verified_company",
                        "severity": "safe", # Changed from low to safe
                        "message": f"Company Presence Found: {company_name} has a verified digital footprint on professional networks, though this specific listing was not found."
                    })
                else:
                    # Only flag as high if we found ABSOLUTELY nothing about the company
                    findings.append({
                        "type": "agent_no_record",
                        "severity": "high",
                        "message": f"Unverified Entity: No professional record or career presence found for '{company_name}'. Exercise extreme caution."
                    })

            except Exception as e:
                print(f"Platform Verification Error: {e}")
                
        return findings

    @staticmethod
    async def verify_official_careers(company_name: str, job_title: str) -> List[Dict]:
        """
        Targeted search for the specific job opening on the company's official career site.
        """
        findings = []
        api_key = PlatformVerifier._get_api_key()
        if not company_name or not job_title or not api_key:
            return findings

        # Sanitize and URL encode
        name = PlatformVerifier._sanitize(company_name).lower().replace(" ", "")
        title = PlatformVerifier._sanitize(job_title)
        
        async with httpx.AsyncClient() as client:
            # 🔍 Specific query for the company's official domain + job
            query = quote_plus(f'site:careers.{name}.com "{title}" OR site:{name}.com/careers "{title}"')
            url = f"https://serpapi.com/search.json?q={query}&api_key={api_key}"
            
            try:
                response = await client.get(url)
                data = response.json()
                organic = data.get("organic_results", [])
                
                if organic:
                    findings.append({
                        "type": "official_site_match",
                        "severity": "safe",
                        "message": f"Official Source: Found direct job listing for '{job_title}' on {company_name}'s official career portal."
                    })
                else:
                    findings.append({
                        "type": "no_official_listing",
                        "severity": "medium",
                        "message": f"Missing Official Listing: Job for '{job_title}' was not found on the primary company careers page. Verify via official contact."
                    })
            except Exception as e:
                print(f"Official Site Verification Error: {e}")
                
        return findings

    @staticmethod
    async def verify_company_location(company_name: str) -> List[Dict]:
        """
        Verifies the company's physical presence (location) via Knowledge Graph.
        """
        findings = []
        api_key = PlatformVerifier._get_api_key()
        if not company_name or not api_key:
            return findings

        # Sanitize and URL encode
        name = PlatformVerifier._sanitize(company_name)
        
        async with httpx.AsyncClient() as client:
            query = quote_plus(f'"{name}" headquarter address location')
            url = f"https://serpapi.com/search.json?q={query}&api_key={api_key}"
            
            try:
                response = await client.get(url)
                data = response.json()
                knowledge_graph = data.get("knowledge_graph", {})
                
                address = knowledge_graph.get("address")
                if address:
                    findings.append({
                        "type": "company_location_found",
                        "severity": "safe",
                        "message": f"Verified Headquarters: {company_name} is physically located at {address}."
                    })
                else:
                    findings.append({
                        "type": "company_location_missing",
                        "severity": "medium",
                        "message": f"Unverified Location: No registered physical address or headquarters found for '{company_name}' via Knowledge Graph."
                    })
            except Exception as e:
                print(f"Company Location Error: {e}")
                
        return findings
