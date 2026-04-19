import html
import json
import re
from html.parser import HTMLParser
from typing import Any

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobMatchCV/1.0"
MAX_TEXT_LENGTH = 12000


def _normalize_space(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _html_to_text_preserving_blocks(raw_html: str) -> str:
    class VisibleTextParser(HTMLParser):
        SKIP_TAGS = {"script", "style", "noscript", "svg"}
        BLOCK_TAGS = {
            "p",
            "div",
            "section",
            "article",
            "li",
            "ul",
            "ol",
            "br",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        }

        def __init__(self):
            super().__init__()
            self.parts: list[str] = []
            self.skip_depth = 0

        def handle_starttag(self, tag: str, attrs):
            if tag in self.SKIP_TAGS:
                self.skip_depth += 1
                return
            attrs_dict = dict(attrs)
            combined = " ".join(
                value for key, value in attrs_dict.items() if key in {"class", "id", "aria-label"} and value
            ).lower()
            if any(
                token in combined
                for token in {"footer", "header", "nav", "cookie", "privacy", "application", "apply", "alert"}
            ):
                self.skip_depth += 1
                return
            if self.skip_depth == 0 and tag in self.BLOCK_TAGS:
                self.parts.append("\n")

        def handle_endtag(self, tag: str):
            if self.skip_depth > 0:
                self.skip_depth -= 1
                return
            if tag in self.BLOCK_TAGS:
                self.parts.append("\n")

        def handle_data(self, data: str):
            if self.skip_depth > 0:
                return
            text = _normalize_space(data)
            if text:
                self.parts.append(text)

    parser = VisibleTextParser()
    parser.feed(raw_html)
    text = "\n".join(part for part in parser.parts if part.strip())
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _extract_json_ld_blocks(raw_html: str) -> list[Any]:
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.IGNORECASE | re.DOTALL,
    )
    blocks: list[Any] = []
    for match in pattern.findall(raw_html):
        payload = html.unescape(match).strip()
        if not payload:
            continue
        try:
            blocks.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return blocks


def _find_job_posting_description(node: Any) -> tuple[str, str] | None:
    if isinstance(node, dict):
        node_type = node.get("@type")
        types = [node_type] if isinstance(node_type, str) else node_type or []
        if any(str(item).lower() == "jobposting" for item in types if item):
            description = node.get("description")
            title = node.get("title") or node.get("name") or ""
            if isinstance(description, str) and description.strip():
                return _normalize_space(description), _normalize_space(str(title))
        for value in node.values():
            found = _find_job_posting_description(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_job_posting_description(item)
            if found:
                return found
    return None


def _extract_meta_description(raw_html: str) -> str:
    patterns = [
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_html, re.IGNORECASE | re.DOTALL)
        if match:
            return _normalize_space(match.group(1))
    return ""


def _clean_extracted_text(text: str) -> str:
    lines = [line.strip() for line in re.split(r"[\r\n]+", text)]
    kept: list[str] = []
    for line in lines:
        if not line:
            continue
        lower = line.lower()
        if any(
            token in lower
            for token in {
                "privacy notice",
                "create alert",
                "create a job alert",
                "apply for this job",
                "accepted file types",
                "powered by",
                "how did you hear about this job",
                "first name",
                "last name",
                "country*",
                "phone*",
                "resume/cv*",
                "cover letter",
            }
        ):
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:MAX_TEXT_LENGTH].strip()


def _to_adzuna_details_url(url: str) -> str:
    match = re.search(r"adzuna\.com/land/ad/(\d+)", url)
    if not match:
        return url
    job_id = match.group(1)
    return f"https://www.adzuna.com/details/{job_id}?utm_medium=api"


def fetch_job_page_text(url: str) -> dict[str, str]:
    request_url = _to_adzuna_details_url(url)
    response = requests.get(
        request_url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()

    raw_html = response.text
    for block in _extract_json_ld_blocks(raw_html):
        extracted = _find_job_posting_description(block)
        if extracted:
            text, title = extracted
            return {
                "requested_url": url,
                "fetched_url": response.url,
                "page_title": title,
                "page_text": _clean_extracted_text(text),
                "source": "json-ld",
            }

    meta_description = _extract_meta_description(raw_html)
    visible_text = _html_to_text_preserving_blocks(raw_html)
    combined = "\n\n".join(part for part in [meta_description, visible_text] if part)

    return {
        "requested_url": url,
        "fetched_url": response.url,
        "page_title": "",
        "page_text": _clean_extracted_text(combined),
        "source": "html",
    }
