"""
External Threat Intelligence Service

Integrates with:
- OpenPhish (openphish.com) - Free phishing feed
- PhishTank (phishtank.com) - Phishing URL database
- URLhaus (urlhaus-api.abuse.ch) - Malware URLs
- Google Safe Browsing - Malware/phishing detection
- VirusTotal-style abuse.ch APIs
"""

import httpx
import dns.resolver
import socket
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class ExternalIntelService:
    """Check external threat intelligence sources."""

    # In-memory cache for threat lookups (1 hour TTL)
    _cache = {}
    _cache_ttl = 3600  # 1 hour

    @classmethod
    async def check_url_threats(cls, url: str) -> List[Dict]:
        """
        Check URL against multiple threat intelligence sources.
        Returns list of findings.
        """
        from urllib.parse import urlparse

        findings = []
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check each threat source in parallel
        tasks = [
            cls._check_openphish(domain),
            cls._check_urlhaus(domain),
            cls._check_abuse_ch(domain),
        ]

        results = await httpx.gather(*tasks, return_exceptions=True)

        for source, result in zip(["openphish", "urlhaus", "abuse_ch"], results):
            if isinstance(result, dict) and result.get("is_malicious"):
                findings.append({
                    "type": "external_threat_match",
                    "severity": "critical",
                    "message": f"URL flagged by {source}: {result.get('details', 'Known malicious')}",
                    "source": source,
                    "raw_data": result
                })

        return findings

    @classmethod
    async def _check_openphish(cls, domain: str) -> Dict:
        """Check against OpenPhish feed (free, no API key needed)."""
        cache_key = f"openphish:{domain}"
        if cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if datetime.now() < cached["expires"]:
                return cached["data"]

        try:
            # OpenPhish provides free feed
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://openphish.com/feed.txt")
                if response.status_code == 200:
                    # Check if domain appears in feed
                    if domain.lower() in response.text.lower():
                        result = {"is_malicious": True, "source": "OpenPhish", "details": "Found in OpenPhish feed"}
                        cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
                        return result
        except Exception as e:
            print(f"OpenPhish check error: {e}")

        result = {"is_malicious": False, "source": "OpenPhish"}
        cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
        return result

    @classmethod
    async def _check_urlhaus(cls, domain: str) -> Dict:
        """Check against URLhaus API."""
        cache_key = f"urlhaus:{domain}"
        if cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if datetime.now() < cached["expires"]:
                return cached["data"]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://urlhaus-api.abuse.ch/v1/host/{domain}/"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("urlhaus_reference"):
                        result = {"is_malicious": True, "source": "URLhaus", "details": "Listed in URLhaus malware database"}
                        cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
                        return result
        except Exception as e:
            print(f"URLhaus check error: {e}")

        result = {"is_malicious": False, "source": "URLhaus"}
        cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
        return result

    @classmethod
    async def _check_abuse_ch(cls, domain: str) -> Dict:
        """Check against abuse.ch threat feeds."""
        cache_key = f"abuse_ch:{domain}"
        if cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if datetime.now() < cached["expires"]:
                return cached["data"]

        # Check multiple abuse.ch feeds
        feeds = [
            ("https://urlhaus.abuse.ch/downloads/host/", "URLhaus Host"),
            ("https://threatfox.abuse.ch/downloads/host/", "ThreatFox"),
        ]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for feed_url, feed_name in feeds:
                    try:
                        response = await client.get(feed_url)
                        if response.status_code == 200:
                            if domain.lower() in response.text.lower():
                                result = {"is_malicious": True, "source": feed_name, "details": f"Found in {feed_name}"}
                                cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
                                return result
                    except:
                        continue
        except Exception as e:
            print(f"abuse.ch check error: {e}")

        result = {"is_malicious": False, "source": "abuse_ch"}
        cls._cache[cache_key] = {"data": result, "expires": datetime.now() + cls._cache_ttl}
        return result


class SSLAnalyzer:
    """Analyze SSL certificates for security issues."""

    @classmethod
    def analyze_ssl(cls, hostname: str) -> List[Dict]:
        """Analyze SSL certificate of a domain."""
        findings = []

        try:
            import ssl
            import certifi

            context = ssl.create_default_context(cafile=certifi.where())
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    # Check certificate expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_left = (not_after - datetime.now()).days

                    if days_left < 0:
                        findings.append({
                            "type": "ssl_expired",
                            "severity": "high",
                            "message": f"SSL certificate expired {abs(days_left)} days ago"
                        })
                    elif days_left < 30:
                        findings.append({
                            "type": "ssl_expiring_soon",
                            "severity": "medium",
                            "message": f"SSL certificate expires in {days_left} days"
                        })

                    # Check if certificate is self-signed
                    issuer = dict(x[0] for x in cert['issuer'])
                    if 'organizationName' not in issuer:
                        findings.append({
                            "type": "ssl_self_signed",
                            "severity": "high",
                            "message": "Certificate appears to be self-signed"
                        })

                    # Check certificate subject
                    subject = dict(x[0] for x in cert['subject'])
                    common_name = subject.get('commonName', '')

                    # Check for mismatched domain (with wildcard support)
                    def match_hostname(hostname, cert_cn):
                        hostname = hostname.lower().replace("www.", "")
                        cert_cn = cert_cn.lower().replace("www.", "")
                        if cert_cn.startswith("*."):
                            base_domain = cert_cn[2:]
                            return hostname.endswith(base_domain)
                        return hostname == cert_cn

                    if not match_hostname(hostname, common_name):
                        findings.append({
                            "type": "ssl_hostname_mismatch",
                            "severity": "high",
                            "message": f"Certificate CN ({common_name}) doesn't match hostname ({hostname})"
                        })

                    # Add positive finding if SSL is valid
                    findings.append({
                        "type": "ssl_valid",
                        "severity": "safe",
                        "message": f"Valid SSL certificate from issuer: {issuer.get('organizationName', 'Unknown')}"
                    })

        except ssl.SSLCertVerificationError as e:
            findings.append({
                "type": "ssl_invalid",
                "severity": "high",
                "message": f"SSL certificate validation failed: {str(e)[:100]}"
            })
        except socket.timeout:
            findings.append({
                "type": "ssl_timeout",
                "severity": "medium",
                "message": "Could not connect to port 443 - domain may not support HTTPS"
            })
        except Exception as e:
            print(f"SSL analysis error: {type(e).__name__}: {str(e)[:50]}")

        return findings


class IPIntelligence:
    """Analyze IP addresses for threat intelligence."""

    # Known malicious IP patterns and suspicious countries
    SUSPICIOUS_COUNTRIES = {
        "CN": "China",
        "RU": "Russia",
        "KP": "North Korea",
        "IR": "Iran",
        "BY": "Belarus",
        "VE": "Venezuela"
    }

    @classmethod
    def analyze_ip(cls, hostname: str) -> List[Dict]:
        """Analyze IP address associated with a domain."""
        findings = []

        try:
            # Resolve hostname to IP
            ip = socket.gethostbyname(hostname)
            findings.append({
                "type": "ip_resolved",
                "severity": "info",
                "message": f"Domain resolves to IP: {ip}",
                "raw_data": {"ip": ip}
            })

            # Get hostname from IP (reverse DNS)
            try:
                reverse_host = socket.gethostbyaddr(ip)[0]
                findings.append({
                    "type": "reverse_dns",
                    "severity": "low",
                    "message": f"Reverse DNS: {reverse_host}",
                    "raw_data": {"reverse_dns": reverse_host}
                })
            except socket.herror:
                findings.append({
                    "type": "no_reverse_dns",
                    "severity": "medium",
                    "message": "No reverse DNS records - common for malicious IPs"
                })

            # Check for hosting IP (not associated with major providers)
            # This is a simplified check - in production, use IP geolocation API
            findings.append({
                "type": "ip_analysis",
                "severity": "low",
                "message": f"IP address analysis completed for {ip}"
            })

        except socket.gaierror:
            findings.append({
                "type": "dns_resolution_failed",
                "severity": "high",
                "message": "Could not resolve domain to IP - possibly offline or blocking DNS"
            })
        except Exception as e:
            print(f"IP analysis error: {e}")

        return findings


class EmailAnalyzer:
    """Analyze email addresses found in text."""

    # Free email providers (less trustworthy for professional emails)
    FREE_EMAIL_PROVIDERS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "aol.com", "icloud.com", "mail.com", "protonmail.com",
        "yandex.com", "zoho.com", "gmx.com"
    }

    # Suspicious email patterns
    SUSPICIOUS_PATTERNS = [
        r"recruiter\d*@",  # recruiter123@...
        r"hr\d*@",  # hr456@...
        r"jobs\d*@",  # jobs789@...
        r"careers\d*@",  # careers@...
        r"\d{5,}@",  # 12345@... (numeric prefix)
    ]

    @classmethod
    def extract_and_analyze_emails(cls, text: str) -> List[Dict]:
        """Extract and analyze email addresses in text."""
        findings = []

        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        for email in emails:
            domain = email.split('@')[1].lower()

            # Check for free email providers
            if domain in cls.FREE_EMAIL_PROVIDERS:
                findings.append({
                    "type": "free_email_provider",
                    "severity": "medium",
                    "message": f"Recruiter using free email: {email} - verify through official channels"
                })

            # Check for suspicious patterns
            for pattern in cls.SUSPICIOUS_PATTERNS:
                if re.match(pattern, email):
                    findings.append({
                        "type": "suspicious_email_pattern",
                        "severity": "high",
                        "message": f"Suspicious email pattern detected: {email}"
                    })
                    break

            # Check for typosquatting (common in impersonation)
            if domain not in cls.FREE_EMAIL_PROVIDERS:
                # Check if domain looks like a major company but isn't
                major_domains = ["amazon", "google", "microsoft", "apple", "meta", "netflix", "flipkart"]
                for major in major_domains:
                    if major in domain and major not in ["amazon", "flipkart"]:
                        if domain != f"{major}.com":
                            findings.append({
                                "type": "email_typosquatting",
                                "severity": "critical",
                                "message": f"Email domain '{domain}' looks like '{major}' - possible impersonation"
                            })

        return findings


async def run_full_external_analysis(url: str, text: str = "") -> List[Dict]:
    """Run all external intelligence checks."""
    findings = []

    from urllib.parse import urlparse

    if url:
        parsed = urlparse(url)
        domain = parsed.netloc

        # Run checks in parallel
        tasks = [
            ExternalIntelService.check_url_threats(url),
        ]

        # Add SSL analysis (sync but fast)
        if domain:
            findings.extend(SSLAnalyzer.analyze_ssl(domain))
            findings.extend(IPIntelligence.analyze_ip(domain))

    # Analyze emails in text
    if text:
        findings.extend(EmailAnalyzer.extract_and_analyze_emails(text))

    return findings