"""Download and extract arXiv full text (PDF preferred, HTML fallback)."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pypdf import PdfReader


USER_AGENT = "ArxivCount/0.1 (research; local; +https://justinzyc271828-sys.github.io/)"


def _http_get(url: str, timeout: int = 60) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def pdf_url(arxiv_id: str) -> str:
    aid = arxiv_id.strip()
    return f"https://arxiv.org/pdf/{aid}.pdf"


def html_url(arxiv_id: str) -> str:
    aid = arxiv_id.strip()
    return f"https://arxiv.org/html/{aid}"


def sanitize_text(text: str) -> str:
    """Remove lone surrogates and other non-UTF8-safe chars for disk write."""
    if not text:
        return ""
    # Drop UTF-16 surrogate code points that sometimes appear in PDF extracts
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text


def extract_pdf_text(pdf_path: Path, max_pages: int | None = None) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    pages = reader.pages
    n = len(pages) if max_pages is None else min(len(pages), max_pages)
    for i in range(n):
        try:
            t = pages[i].extract_text() or ""
        except Exception:  # noqa: BLE001
            t = ""
        if t.strip():
            parts.append(t)
    text = "\n\n".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return sanitize_text(text.strip())


def extract_html_text(html_bytes: bytes) -> str:
    # lightweight strip tags (avoid heavy deps)
    raw = html_bytes.decode("utf-8", errors="ignore")
    raw = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    raw = re.sub(r"&nbsp;", " ", raw)
    raw = re.sub(r"&amp;", "&", raw)
    raw = re.sub(r"&lt;", "<", raw)
    raw = re.sub(r"&gt;", ">", raw)
    raw = re.sub(r"\s+", " ", raw)
    return sanitize_text(raw.strip())


def download_fulltext(
    arxiv_id: str,
    downloads_dir: Path,
    *,
    delay: float = 1.0,
    force: bool = False,
) -> dict[str, Any]:
    """Download PDF (and optional HTML fallback). Returns metadata + local paths."""
    downloads_dir.mkdir(parents=True, exist_ok=True)
    safe = arxiv_id.replace("/", "_")
    pdf_path = downloads_dir / f"{safe}.pdf"
    txt_path = downloads_dir / f"{safe}.txt"
    meta: dict[str, Any] = {
        "arxiv_id": arxiv_id,
        "pdf_path": str(pdf_path) if pdf_path.exists() else None,
        "txt_path": str(txt_path) if txt_path.exists() else None,
        "source": None,
        "chars": 0,
        "ok": False,
        "error": None,
    }

    if txt_path.exists() and not force:
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        meta.update(source="cache", chars=len(text), ok=bool(text.strip()), txt_path=str(txt_path))
        if pdf_path.exists():
            meta["pdf_path"] = str(pdf_path)
        return meta

    text = ""
    source = None
    err = None

    # Candidate PDF URLs (versionless + export + v1)
    pdf_urls = [
        pdf_url(arxiv_id),
        f"https://export.arxiv.org/pdf/{arxiv_id}.pdf",
        f"https://arxiv.org/pdf/{arxiv_id}v1.pdf",
        f"https://export.arxiv.org/pdf/{arxiv_id}v1.pdf",
    ]
    html_urls = [
        html_url(arxiv_id),
        f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}",
    ]

    # 1) PDF
    try:
        if force or not pdf_path.exists() or pdf_path.stat().st_size < 1000:
            last_pdf_err = None
            for u in pdf_urls:
                try:
                    data = _http_get(u)
                    if data[:4] == b"%PDF" or len(data) > 2000:
                        pdf_path.write_bytes(data)
                        time.sleep(delay)
                        last_pdf_err = None
                        break
                except Exception as e:  # noqa: BLE001
                    last_pdf_err = e
                    continue
            if last_pdf_err and not pdf_path.exists():
                raise last_pdf_err
        if pdf_path.exists():
            text = extract_pdf_text(pdf_path)
            source = "pdf"
    except Exception as e:  # noqa: BLE001
        err = f"pdf: {type(e).__name__}: {e}"

    # 2) HTML fallback if PDF text too short
    if len(text) < 800:
        for u in html_urls:
            try:
                html = _http_get(u)
                time.sleep(delay)
                htext = extract_html_text(html)
                if len(htext) > len(text):
                    text = htext
                    source = "html"
                    break
            except Exception as e:  # noqa: BLE001
                err = (err or "") + f" | html: {type(e).__name__}: {e}"

    text = sanitize_text(text)
    if text.strip():
        txt_path.write_text(text, encoding="utf-8", errors="ignore")
        meta.update(
            ok=True,
            source=source,
            chars=len(text),
            pdf_path=str(pdf_path) if pdf_path.exists() else None,
            txt_path=str(txt_path),
            error=err,
        )
    else:
        meta.update(ok=False, error=err or "empty text", source=source)

    return meta


def load_text(txt_path: Path) -> str:
    return txt_path.read_text(encoding="utf-8", errors="ignore")


def sample_for_llm(text: str, max_chars: int = 90000) -> str:
    """Keep head + tail so abstract/intro and acknowledgements/refs AI notes are both visible."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.72)
    tail = max_chars - head - 80
    return (
        text[:head]
        + "\n\n[... middle omitted for length ...]\n\n"
        + text[-tail:]
    )
