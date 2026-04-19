"""
Project 1: Regex-Based Web Scraper
====================================
Scrapes and extracts structured data (emails, phones, URLs, names, social handles)
from raw HTML or plain text using compiled Regex patterns.

Use cases: OSINT data extraction, recon during pentests, lead generation,
           security research, data harvesting from public pages.

Author  : Security Engineer
Usage   : python project1_regex_scraper.py --url <URL> [--output results.json]
"""

import re
import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List


# ─────────────────────────────────────────────
#  Compiled Regex Patterns
# ─────────────────────────────────────────────

PATTERNS: Dict[str, re.Pattern] = {

    # RFC-5322 simplified email
    "emails": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    ),

    # International phone numbers  (+91-9876543210, (123) 456-7890, etc.)
    "phones": re.compile(
        r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{4}",
    ),

    # Full URLs (http / https / ftp)
    "urls": re.compile(
        r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^\s\"'<>]*)?",
        re.IGNORECASE,
    ),

    # IPv4 addresses
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    ),

    # Twitter / X handles  (@username)
    "twitter_handles": re.compile(
        r"(?<!\w)@([A-Za-z0-9_]{1,15})(?!\w)",
    ),

    # LinkedIn profile URLs
    "linkedin": re.compile(
        r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?",
        re.IGNORECASE,
    ),

    # GitHub profile / repo URLs
    "github": re.compile(
        r"https?://(?:www\.)?github\.com/[A-Za-z0-9\-]+(?:/[A-Za-z0-9\-._]+)?/?",
        re.IGNORECASE,
    ),

    # Dates  (DD/MM/YYYY, YYYY-MM-DD, Month DD YYYY)
    "dates": re.compile(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}"
        r"|\d{4}[\/\-]\d{2}[\/\-]\d{2}"
        r"|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
        r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    ),

    # Credit card patterns (for demo / pentesting scope only)
    "credit_cards": re.compile(
        r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})\b",
    ),

    # PAN (India)
    "pan_india": re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    ),
}


# ─────────────────────────────────────────────
#  HTML → plain text stripper (no dependencies)
# ─────────────────────────────────────────────

_TAG_RE   = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

def strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = _TAG_RE.sub(" ", html)
    return _SPACE_RE.sub(" ", text).strip()


# ─────────────────────────────────────────────
#  Core extractor
# ─────────────────────────────────────────────

def extract_all(text: str, clean_html: bool = True) -> Dict[str, List[str]]:
    """
    Run all patterns against `text`.
    Returns a dict keyed by pattern name with deduplicated match lists.
    """
    if clean_html:
        text = strip_html(text)

    results: Dict[str, List[str]] = {}
    for name, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        # Flatten tuples from groups, deduplicate, sort
        flat = []
        for m in matches:
            flat.append(m if isinstance(m, str) else m[0])
        results[name] = sorted(set(flat))

    return results


# ─────────────────────────────────────────────
#  HTTP fetch  (stdlib only, no requests)
# ─────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return the response body as a string."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        print(f"[!] HTTP {e.code} for {url}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"[!] URL error: {e.reason}", file=sys.stderr)
        raise


# ─────────────────────────────────────────────
#  Report printer
# ─────────────────────────────────────────────

COLORS = {
    "reset"  : "\033[0m",
    "bold"   : "\033[1m",
    "green"  : "\033[92m",
    "yellow" : "\033[93m",
    "cyan"   : "\033[96m",
    "red"    : "\033[91m",
}


def _c(key: str, text: str) -> str:
    return f"{COLORS[key]}{text}{COLORS['reset']}"


def print_report(results: Dict[str, List[str]], source: str) -> None:
    print()
    print(_c("bold", "=" * 60))
    print(_c("cyan", f"  REGEX SCRAPER RESULTS"))
    print(_c("bold", f"  Source : ") + source)
    print(_c("bold", f"  Time   : ") + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(_c("bold", "=" * 60))

    total = 0
    for category, items in results.items():
        count = len(items)
        total += count
        label = category.replace("_", " ").upper()
        color = "green" if count else "yellow"
        print(f"\n  {_c(color, f'[{label}]')}  ({count} found)")
        for item in items:
            print(f"    • {item}")

    print()
    print(_c("bold", f"  Total matches : {total}"))
    print(_c("bold", "=" * 60))
    print()


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Regex-based web scraper — extracts structured data from any URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project1_regex_scraper.py --url https://example.com
  python project1_regex_scraper.py --url https://example.com --output out.json
  python project1_regex_scraper.py --file page.html
  echo "contact@test.com +91-9876543210" | python project1_regex_scraper.py --stdin
        """,
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--url",   help="Fetch and scrape a live URL")
    src.add_argument("--file",  help="Scrape a local HTML/text file")
    src.add_argument("--stdin", action="store_true", help="Read from stdin")

    p.add_argument("--output",    help="JSON output filename (default: scrape_<timestamp>.json)")
    p.add_argument("--no-color",  action="store_true", help="Disable ANSI colors")
    p.add_argument("--raw",       action="store_true",
                   help="Skip HTML stripping (treat input as plain text)")
    p.add_argument("--patterns",  nargs="+",
                   choices=list(PATTERNS.keys()),
                   help="Run only specific patterns (default: all)")
    return p.parse_args()


def main() -> None:
    args = build_args()

    if args.no_color:
        for k in COLORS:
            COLORS[k] = ""

    # ── Load content ──────────────────────────────────
    if args.url:
        print(f"[*] Fetching {args.url} …")
        content = fetch_url(args.url)
        source  = args.url
    elif args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        source = args.file
    else:
        content = sys.stdin.read()
        source  = "<stdin>"

    # ── Filter patterns if requested ─────────────────
    global PATTERNS
    if args.patterns:
        PATTERNS = {k: v for k, v in PATTERNS.items() if k in args.patterns}

    # ── Extract ───────────────────────────────────────
    results = extract_all(content, clean_html=not args.raw)

    # ── Display ───────────────────────────────────────
    print_report(results, source)

    # ── Save ──────────────────────────────────────────
    # Default output filename: scrape_YYYYMMDD_HHMMSS.json
    out_file = args.output or f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "source"    : source,
        "timestamp" : datetime.now().isoformat(),
        "results"   : results,
    }
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"[+] Results saved to {out_file}\n")

    # Also write a human-readable .txt summary alongside the JSON
    txt_file = out_file.replace(".json", ".txt")
    with open(txt_file, "w", encoding="utf-8") as fh:
        fh.write(f"Regex Scraper Results\n")
        fh.write(f"Source    : {source}\n")
        fh.write(f"Timestamp : {payload['timestamp']}\n")
        fh.write("=" * 60 + "\n\n")
        total = 0
        for category, items in results.items():
            fh.write(f"[{category.upper().replace('_', ' ')}]  ({len(items)} found)\n")
            for item in items:
                fh.write(f"  • {item}\n")
            fh.write("\n")
            total += len(items)
        fh.write(f"Total matches: {total}\n")
    print(f"[+] Human-readable summary saved to {txt_file}\n")


if __name__ == "__main__":
    main()