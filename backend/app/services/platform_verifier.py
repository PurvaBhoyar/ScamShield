import httpx
from app.core.config import settings
from typing import List, Dict

class PlatformVerifier:
    @staticmethod
    async def verify_job_publicly(company_name: str, job_title: str) -> List[Dict]:
        """
        Uses SerpAPI to search for the job listing on official career pages and LinkedIn.
        If found, it returns a 'Trust Bonus' (negative points).
        If not found, it flags a warning.
        """
        findings = []
        if not company_name or not job_title or not settings.SERPAPI_API_KEY:
            return findings
            
        async with httpx.AsyncClient() as client:
            # 🔍 Query 1: LinkedIn/Job Boards for specific Job
            query_job = f'LinkedIn Internshala Glassdoor "{company_name}" "{job_title}"'
            url_job = f"https://serpapi.com/search.json?q={query_job}&api_key={settings.SERPAPI_API_KEY}"
            
            # 🔍 Query 2: Company Presence
            query_company = f'"{company_name}" official careers page LinkedIn profile'
            url_company = f"https://serpapi.com/search.json?q={query_company}&api_key={settings.SERPAPI_API_KEY}"

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
                for res in organic_job[:5]:
                    link = res.get("link", "").lower()
                    if any(p in link for p in ["linkedin.com/jobs", "internshala.com", "glassdoor.com", "naukri.com"]):
                        found_on_platform = True
                        break
                
                # 2. Check for company existence
                found_company = False
                for res in organic_company[:5]:
                    link = res.get("link", "").lower()
                    if any(p in link for p in ["linkedin.com/company", "careers", "about-us"]):
                        found_company = True
                        break

                if found_on_platform:
                    findings.append({
                        "type": "agent_verified_job",
                        "severity": "safe",
                        "message": f"Verified: Job listing found for {company_name} on a major platform."
                    })
                elif found_company:
                    findings.append({
                        "type": "agent_verified_company",
                        "severity": "low",
                        "message": f"Company {company_name} exists on LinkedIn/Web, but this specific job title wasn't found."
                    })
                else:
                    findings.append({
                        "type": "agent_no_record",
                        "severity": "high",
                        "message": f"Warning: No matching record found for {company_name} on professional networks."
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
        if not company_name or not job_title or not settings.SERPAPI_API_KEY:
            return findings

        async with httpx.AsyncClient() as client:
            # 🔍 Specific query for the company's official domain + job
            query = f'site:careers.{company_name.lower().replace(" ", "")}.com "{job_title}" OR site:{company_name.lower().replace(" ", "")}.com/careers "{job_title}"'
            url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"
            
            try:
                response = await client.get(url)
                data = response.json()
                organic = data.get("organic_results", [])
                
                if organic:
                    findings.append({
                        "type": "official_site_match",
                        "severity": "safe",
                        "message": f"Found direct match for '{job_title}' on {company_name}'s official career domain."
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
        if not company_name or not settings.SERPAPI_API_KEY:
            return findings

        async with httpx.AsyncClient() as client:
            query = f'"{company_name}" headquarter address location'
            url = f"https://serpapi.com/search.json?q={query}&api_key={settings.SERPAPI_API_KEY}"
            
            try:
                response = await client.get(url)
                data = response.json()
                knowledge_graph = data.get("knowledge_graph", {})
                
                address = knowledge_graph.get("address")
                if address:
                    findings.append({
                        "type": "company_location_found",
                        "severity": "safe",
                        "message": f"Verified physical location for {company_name}: {address}"
                    })
                else:
                    findings.append({
                        "type": "company_location_missing",
                        "severity": "medium",
                        "message": f"Could not verify a physical office location for {company_name}."
                    })
            except Exception as e:
                print(f"Company Location Error: {e}")
                
        return findings
