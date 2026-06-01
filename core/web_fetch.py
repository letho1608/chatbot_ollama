import os
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Iterable, List, Set
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx

from core.config import SECURITY_KEYWORDS


DEFAULT_ALLOWED_DOMAINS = [
    "cisa.gov",
    "nvd.nist.gov",
    "nist.gov",
    "owasp.org",
    "mitre.org",
    "attack.mitre.org",
    "sans.org",
    "cloudflare.com",
    "learn.microsoft.com",
    "security.googleblog.com",
]
WEB_FETCH_RESULTS = int(os.getenv("WEB_FETCH_RESULTS", "3"))
WEB_FETCH_TIMEOUT = float(os.getenv("WEB_FETCH_TIMEOUT", "8"))
WEB_FETCH_SEARCH_URL = os.getenv("WEB_FETCH_SEARCH_URL", "https://html.duckduckgo.com/html/")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:+#-]*")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "who", "why", "with",
}


@dataclass(frozen=True)
class WebFetchResult:
    title: str
    url: str
    snippet: str
    score: float

    @property
    def content(self) -> str:
        return f"Web context: {self.title}\nSource: {self.url}\n{self.snippet}"


def is_enabled() -> bool:
    return os.getenv("WEB_FETCH_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def allowed_domains() -> List[str]:
    raw = os.getenv("WEB_FETCH_ALLOWED_DOMAINS", "")
    domains = [d.strip().lower() for d in raw.split(",") if d.strip()] if raw else DEFAULT_ALLOWED_DOMAINS
    return [d[4:] if d.startswith("www.") else d for d in domains]


def is_cybersecurity_query(query: str) -> bool:
    query_lower = query.lower()
    if CVE_RE.search(query):
        return True
    return any(keyword.lower() in query_lower for keyword in SECURITY_KEYWORDS)


def retrieve_web_context(query: str, top_k: int = WEB_FETCH_RESULTS) -> List[tuple[str, float]]:
    return [(result.content, result.score) for result in fetch_web_results(query, top_k=top_k)]


def fetch_web_results(query: str, top_k: int = WEB_FETCH_RESULTS) -> List[WebFetchResult]:
    if not is_enabled() or not is_cybersecurity_query(query):
        return []

    urls = direct_allowed_urls(query)
    urls.extend(search_allowed_web(query, max_results=max(top_k * 3, top_k)))
    urls = list(dict.fromkeys(urls))
    if not urls:
        return []

    query_tokens = _tokens(query)
    results: List[WebFetchResult] = []
    with httpx.Client(
        timeout=WEB_FETCH_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0"},
    ) as client:
        for url in urls:
            if len(results) >= top_k:
                break
            try:
                resp = client.get(url)
                content_type = resp.headers.get("content-type", "")
                if resp.status_code >= 400 or not _is_supported_content_type(content_type):
                    continue
                title = _extract_title(resp.text) or urlparse(str(resp.url)).netloc
                text = resp.text if "json" in content_type else _extract_text(resp.text)
                snippet = _best_snippet(text, query_tokens)
                if not snippet:
                    continue
                score = _score_text(title + " " + snippet, query_tokens)
                results.append(WebFetchResult(title=title, url=str(resp.url), snippet=snippet, score=score))
            except httpx.HTTPError:
                continue

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


def direct_allowed_urls(query: str) -> List[str]:
    query_lower = query.lower()
    urls: List[str] = []
    cves = sorted({match.upper() for match in CVE_RE.findall(query)})
    for cve in cves[:3]:
        urls.append(f"https://nvd.nist.gov/vuln/detail/{cve}")

    if any(term in query_lower for term in ("cve", "vulnerability", "advisory", "latest", "recent", "current", "kev", "known exploited", "mới nhất", "cảnh báo")):
        urls.extend([
            "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "https://nvd.nist.gov/vuln",
        ])
    if "owasp" in query_lower or "top 10" in query_lower:
        urls.append("https://owasp.org/www-project-top-ten/")
    if "mitre" in query_lower or "attack" in query_lower:
        urls.append("https://attack.mitre.org/")

    domains = allowed_domains()
    return [url for url in urls if _is_allowed_url(url, domains)]


def search_allowed_web(query: str, max_results: int = 6) -> List[str]:
    domains = allowed_domains()
    domain_filter = " OR ".join(f"site:{domain}" for domain in domains[:8])
    search_query = f"{domain_filter} {query} cybersecurity"
    url = f"{WEB_FETCH_SEARCH_URL}?q={quote_plus(search_query)}"
    try:
        with httpx.Client(
            timeout=WEB_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            resp = client.get(url)
            if resp.status_code >= 400:
                return []
    except httpx.HTTPError:
        return []

    parser = _LinkParser()
    parser.feed(resp.text)
    clean_urls = []
    seen = set()
    for href in parser.links:
        resolved = _resolve_search_href(href, WEB_FETCH_SEARCH_URL)
        if not resolved or not _is_allowed_url(resolved, domains):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        clean_urls.append(resolved)
        if len(clean_urls) >= max_results:
            break
    return clean_urls


def _resolve_search_href(href: str, base_url: str) -> str:
    if not href:
        return ""
    href = unescape(href)
    parsed = urlparse(href)
    if parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    if parsed.scheme in {"http", "https"}:
        return href
    return urljoin(base_url, href)


def _is_allowed_url(url: str, domains: Iterable[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def _is_supported_content_type(content_type: str) -> bool:
    return any(kind in content_type for kind in ("text/html", "text/plain", "application/json", "json"))


def _tokens(value: str) -> Set[str]:
    return {token for token in TOKEN_RE.findall(value.lower()) if token not in STOPWORDS}


def _score_text(text: str, query_tokens: Set[str]) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = _tokens(text)
    overlap = query_tokens & text_tokens
    return float(len(overlap)) + len(overlap) / max(len(query_tokens), 1)


def _best_snippet(text: str, query_tokens: Set[str], max_chars: int = 900) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 40:
            continue
        scored.append((_score_text(sentence, query_tokens), sentence))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [sentence for score, sentence in scored[:4] if score > 0]
    snippet = " ".join(selected) if selected else text[:max_chars]
    return snippet[:max_chars].strip()


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", unescape(match.group(1))).strip()


def _extract_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href", "")
        if href:
            self.links.append(href)


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "noscript", "svg", "head"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "noscript", "svg", "head"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if not self._skip_depth and data.strip():
            self.parts.append(unescape(data.strip()))
