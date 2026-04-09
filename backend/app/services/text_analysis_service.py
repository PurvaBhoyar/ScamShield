"""
Text Analysis Service

Detects:
- AI-generated text patterns
- Grammar/readability issues
- Suspicious text patterns
- Template-like behavior
"""

import re
from typing import List, Dict


class TextAnalysisService:
    """Analyze text for AI-generated content and quality issues."""

    # AI-generated text patterns (common in scam messages)
    AI_PATTERNS = [
        # Excessive hedging
        r"\b(may|might|could|possibly|perhaps)\b.*?\b(may|might|could|possibly|perhaps)\b",
        # Generic professional language
        r"\bkindly\b.*?\bkindly\b",
        # Template phrases
        r"congratulations.*?selected",
        r"earn\s+\d+\s+per\s+day",
        r"no\s+experience\s+required",
        r"work\s+from\s+home",
        r"part\s*time",
        # All caps for emphasis
        r"\b(URGENT|IMMEDIATE|LIMITED|ACT\s+NOW)\b",
        # Excessive punctuation
        r"[!?]{2,}",
    ]

    # Grammar/quality red flags
    GRAMMAR_RED_FLAGS = [
        # Common typos in scam text
        r"\b(adhaar|aadhar)\b",  # Misspelled Aadhaar
        r"\b(ph|f)\s+one\b",  # "ph one" instead of "phone"
        r"\b(w|a)ats\s*app\b",  # Misspelled WhatsApp
        r"\b(t|c)elegram\b",  # Misspelled Telegram
        # Repeated words
        r"\b(\w+)\s+\1\b",
        # Missing spaces
        r"[a-z][A-Z][a-z]",
    ]

    # Readability issues
    READABILITY_PATTERNS = [
        # All CAPS SENTENCES
        r"^[A-Z\s]{30,}$",
        # Numbers disguised as words (common in scams)
        r"(Rs\.?|INR|Rupees)\s*\d+",
        # Excessive numbers
        r"\d{4,}",  # 4+ digit numbers
    ]

    # Suspicious URL patterns in text
    URL_PATTERNS = [
        r"bit\.ly/\w+",
        r"tinyurl\.com/\w+",
        r"t\.co/\w+",
        r"goo\.gl/\w+",
        r"ow\.ly/\w+",
    ]

    @classmethod
    def analyze_text(cls, text: str) -> List[Dict]:
        """
        Analyze text for suspicious patterns.
        Returns list of findings.
        """
        findings = []
        text_lower = text.lower()

        # Check for AI-generated patterns
        for pattern in cls.AI_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                findings.append({
                    "type": "ai_generated_pattern",
                    "severity": "medium",
                    "message": f"Detected AI-generated text pattern: '{match.group()[:50]}...'"
                })
                break  # One finding is enough

        # Check for grammar issues
        for pattern in cls.GRAMMAR_RED_FLAGS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                findings.append({
                    "type": "grammar_issue",
                    "severity": "low",
                    "message": f"Potential grammar issue detected: '{match.group()[:50]}'"
                })
                break

        # Check for readability issues
        for pattern in cls.READABILITY_PATTERNS:
            matches = re.findall(pattern, text)
            if len(matches) > 2:  # Multiple issues
                findings.append({
                    "type": "readability_issue",
                    "severity": "low",
                    "message": f"Detected {len(matches)} readability issues in text"
                })
                break

        # Check for shortened URLs
        for pattern in cls.URL_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                findings.append({
                    "type": "shortened_url",
                    "severity": "medium",
                    "message": f"Text contains {len(matches)} shortened URL(s) - common in phishing"
                })
                break

        # Check for excessive capitalization (suspicious)
        caps_words = re.findall(r"\b[A-Z]{5,}\b", text)
        if len(caps_words) > 3:
            findings.append({
                "type": "excessive_caps",
                "severity": "low",
                "message": f"Found {len(caps_words)} words in all caps - typical of scam messages"
            })

        # Check for unrealistic salary claims
        salary_pattern = r"(?:salary|earn|pay)\s*(?: rs\.?| INR | rupees? )?\s*(\d{4,})"
        matches = re.findall(salary_pattern, text, re.IGNORECASE)
        for match in matches:
            if int(match) > 50000:  # More than 50k/month is suspicious for entry-level
                findings.append({
                    "type": "unrealistic_salary",
                    "severity": "high",
                    "message": f"Unrealistic salary claim: Rs. {match}/month - typical scam lure"
                })
                break

        # Check for contact info requests (phone/telegram)
        contact_patterns = [
            r"whatsapp\s*[:\s]*\+\d{1,3}\s*\d{8,10}",
            r"telegram\s*[:\s]*@[\w]+",
            r"call\s+(?:me\s+)?(?:at\s+)?\+\d{1,3}\s*\d{8,10}",
        ]
        for pattern in contact_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append({
                    "type": "informal_contact_request",
                    "severity": "medium",
                    "message": "Requests informal contact via WhatsApp/Telegram - common scam practice"
                })
                break

        return findings


def analyze_text_quality(text: str) -> Dict:
    """
    Quick quality check returning metrics.
    """
    words = text.split()
    sentences = re.split(r"[.!?]+", text)

    return {
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "avg_words_per_sentence": len(words) / max(len(sentences), 1),
        "has_excessive_caps": len(re.findall(r"\b[A-Z]{5,}\b", text)) > 3,
        "has_numbers_disguised": bool(re.search(r"(?:Rs\.?|INR)\s*\d+", text, re.IGNORECASE)),
    }