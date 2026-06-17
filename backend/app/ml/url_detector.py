"""
URL Threat Detector
Extracts URLs from text, applies heuristic scoring for malicious indicators,
and optionally queries VirusTotal or PhishTank APIs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── URL Extraction ───────────────────────────────────────────────────────────
URL_REGEX = re.compile(
    r"https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)",
    re.IGNORECASE,
)

# ─── URL shortener domains ────────────────────────────────────────────────────
SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "shorte.st", "tiny.cc", "bc.vc",
}

# ─── Suspicious TLDs ─────────────────────────────────────────────────────────
SUSPICIOUS_TLDS = {".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".pw", ".top"}

# ─── Phishing keyword patterns in URL ─────────────────────────────────────────
URL_KEYWORD_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(login|signin|verify|account|secure|update|confirm|bank|paypal|amazon)",
        r"(free|win|prize|reward|gift|coupon)",
        r"\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3}",  # IP-like patterns in path
        r"\.php\?",                              # Classic phishing query
        r"(password|passwd|pwd|credential)",
    ]
]


@dataclass
class URLAnalysisResult:
    url: str
    is_shortened: bool = False
    suspicious_tld: bool = False
    keyword_hits: int = 0
    virustotal_malicious: Optional[bool] = None
    heuristic_score: float = 0.0
    reasons: List[str] = field(default_factory=list)


class URLDetector:
    """Extracts and scores URLs for malicious indicators."""

    def extract_urls(self, text: str) -> List[str]:
        """Extract all HTTP/HTTPS URLs from a body of text."""
        return list(set(URL_REGEX.findall(text)))

    def analyze_url(self, url: str) -> URLAnalysisResult:
        result = URLAnalysisResult(url=url)
        score = 0.0

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")

            # Shortened link
            if domain in SHORTENERS:
                result.is_shortened = True
                result.reasons.append(f"URL shortener detected ({domain})")
                score += 30.0

            # Suspicious TLD
            for tld in SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    result.suspicious_tld = True
                    result.reasons.append(f"Suspicious TLD ({tld})")
                    score += 25.0
                    break

            # Keyword patterns in full URL
            full_url_lower = url.lower()
            kw_hits = 0
            for pattern in URL_KEYWORD_PATTERNS:
                if pattern.search(full_url_lower):
                    kw_hits += 1
            if kw_hits:
                result.keyword_hits = kw_hits
                result.reasons.append(f"Phishing keywords in URL ({kw_hits} pattern(s))")
                score += min(kw_hits * 15.0, 40.0)

            # IP address in host (instead of domain)
            ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if ip_pattern.match(domain):
                result.reasons.append("Raw IP address used as host")
                score += 20.0

        except Exception as exc:
            logger.warning(f"URL parsing error for {url}: {exc}")

        result.heuristic_score = round(min(score, 100.0), 2)
        return result

    def analyze_all(self, text: str) -> tuple[List[str], float, List[str]]:
        """
        Extract all URLs from text and compute aggregate URL threat score.

        Returns:
            (extracted_urls, url_score_0_100, reasons)
        """
        urls = self.extract_urls(text)
        if not urls:
            return [], 0.0, []

        results = [self.analyze_url(u) for u in urls]
        all_reasons: List[str] = []
        max_score = 0.0

        for r in results:
            all_reasons.extend(r.reasons)
            max_score = max(max_score, r.heuristic_score)

        return urls, round(max_score, 2), list(set(all_reasons))

    async def query_virustotal(self, url: str) -> Optional[bool]:
        """
        Query VirusTotal URL scan endpoint.
        Returns True if malicious, False if clean, None if unavailable.
        """
        if not settings.VIRUSTOTAL_API_KEY:
            return None
        try:
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"https://www.virustotal.com/api/v3/urls/{url_id}",
                    headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
                )
                if resp.status_code == 200:
                    stats = resp.json()["data"]["attributes"]["last_analysis_stats"]
                    return stats.get("malicious", 0) > 0
        except Exception as exc:
            logger.warning(f"VirusTotal query failed: {exc}")
        return None


url_detector = URLDetector()
