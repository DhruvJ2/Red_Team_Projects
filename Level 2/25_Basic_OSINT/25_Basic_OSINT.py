"""
Project 2: Multi-Engine Search Bot
=====================================
Queries Google, Bing, and Yahoo! programmatically, parses result pages,
and aggregates titles + URLs + snippets into a unified report.

Use cases: OSINT recon, footprinting during pentests, threat intelligence
           gathering, competitive research, vulnerability research.

Author  : Security Engineer
Usage   : python project2_search_bot.py --query "site:target.com" [--engines google bing]
          python project2_search_bot.py --query "intext:admin filetype:sql" --pages 3
"""

import re
import sys
import json
import time
import random
import argparse
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────

@dataclass
class SearchResult:
    engine  : str
    rank    : int
    title   : str
    url     : str
    snippet : str = ""


@dataclass
class SearchReport:
    query     : str
    engines   : List[str]
    timestamp : str = field(default_factory=lambda: datetime.now().isoformat())
    results   : List[SearchResult] = field(default_factory=list)

    def add(self, result: SearchResult) -> None:
        self.results.append(result)

    def unique_urls(self) -> List[str]:
        seen, out = set(), []
        for r in self.results:
            if r.url not in seen:
                seen.add(r.url)
                out.append(r.url)
        return out


# ─────────────────────────────────────────────
#  User-Agent pool  (rotate to avoid blocks)
# ─────────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",

    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


# ─────────────────────────────────────────────
#  Generic HTTP helper
# ─────────────────────────────────────────────

def _get(url: str, timeout: int = 20) -> str:
    """Fetch URL with rotating UA, return HTML string."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent"      : _random_ua(),
            "Accept"          : "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.9",
            "Accept-Encoding" : "identity",       # keep it simple
            "Connection"      : "close",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            cs = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(cs, errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(str(e.reason)) from e


# ─────────────────────────────────────────────
#  HTML utilities
# ─────────────────────────────────────────────

_TAG       = re.compile(r"<[^>]+>")
_ENTITY    = re.compile(r"&(?:#(\d+)|([a-zA-Z]+));")
_WHITESPACE = re.compile(r"\s+")

_ENTITY_MAP = {
    "amp": "&", "lt": "<", "gt": ">", "quot": '"',
    "apos": "'", "nbsp": " ", "mdash": "—", "ndash": "–",
}

def _decode_entities(text: str) -> str:
    def _rep(m: re.Match) -> str:
        if m.group(1):
            return chr(int(m.group(1)))
        fallback: str = m.group(0)
        return _ENTITY_MAP.get(m.group(2), fallback)
    return _ENTITY.sub(_rep, text)

def _clean(html: str) -> str:
    """Strip tags, decode entities, collapse whitespace."""
    text = _TAG.sub(" ", html)
    text = _decode_entities(text)
    return _WHITESPACE.sub(" ", text).strip()


# ─────────────────────────────────────────────
#  Engine: Google
# ─────────────────────────────────────────────

class GoogleParser:
    NAME     = "Google"
    BASE_URL = "https://www.google.com/search"

    # Each result block lives in a <div class="g"> or similar container
    # We parse with regex to avoid third-party deps
    _RESULT_BLOCK = re.compile(
        r'<div[^>]+class="[^"]*(?:g|tF2Cxc)[^"]*"[^>]*>(.*?)</div>\s*</div>',
        re.DOTALL,
    )
    _TITLE   = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL)
    _HREF    = re.compile(r'<a[^>]+href="(https?://[^"&]+)', re.IGNORECASE)
    _SNIPPET = re.compile(
        r'<span[^>]+class="[^"]*(?:aCOpRe|VwiC3b|st)[^"]*"[^>]*>(.*?)</span>',
        re.DOTALL,
    )

    def build_url(self, query: str, page: int = 0) -> str:
        params = urllib.parse.urlencode({
            "q"    : query,
            "start": page * 10,
            "hl"   : "en",
            "num"  : 10,
        })
        return f"{self.BASE_URL}?{params}"

    def parse(self, html: str, engine_name: str) -> List[SearchResult]:
        results = []
        rank = 1

        # Fallback: grab all <a href="https://..."> that look like results
        for href_m in re.finditer(
            r'<a[^>]+href="(https?://(?!(?:www\.google|webcache|accounts))[^"&]+)"',
            html,
            re.IGNORECASE,
        ):
            url = href_m.group(1)

            # Try to find surrounding title text
            start = max(0, href_m.start() - 300)
            chunk = html[start : href_m.end() + 600]

            title_m   = self._TITLE.search(chunk)
            snippet_m = self._SNIPPET.search(chunk)

            title   = _clean(title_m.group(1))   if title_m   else url
            snippet = _clean(snippet_m.group(1)) if snippet_m else ""

            if title and url:
                results.append(SearchResult(engine_name, rank, title, url, snippet))
                rank += 1
                if rank > 10:
                    break

        return results


# ─────────────────────────────────────────────
#  Engine: Bing
# ─────────────────────────────────────────────

class BingParser:
    NAME     = "Bing"
    BASE_URL = "https://www.bing.com/search"

    _RESULT  = re.compile(r'<li[^>]+class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', re.DOTALL)
    _TITLE   = re.compile(r'<h2[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    _SNIPPET = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)

    def build_url(self, query: str, page: int = 0) -> str:
        params = urllib.parse.urlencode({
            "q"    : query,
            "first": page * 10 + 1,
            "form" : "QBLH",
        })
        return f"{self.BASE_URL}?{params}"

    def parse(self, html: str, engine_name: str) -> List[SearchResult]:
        results = []
        rank = 1
        for m in self._RESULT.finditer(html):
            block     = m.group(1)
            title_m   = self._TITLE.search(block)
            snippet_m = self._SNIPPET.search(block)

            if not title_m:
                continue

            url     = title_m.group(1).strip()
            title   = _clean(title_m.group(2))
            snippet = _clean(snippet_m.group(1)) if snippet_m else ""

            if url.startswith("http"):
                results.append(SearchResult(engine_name, rank, title, url, snippet))
                rank += 1

        return results


# ─────────────────────────────────────────────
#  Engine: Yahoo!
# ─────────────────────────────────────────────

class YahooParser:
    NAME     = "Yahoo"
    BASE_URL = "https://search.yahoo.com/search"

    _RESULT  = re.compile(r'<div[^>]+class="[^"]*algo[^"]*"[^>]*>(.*?)</div>', re.DOTALL)
    _TITLE   = re.compile(r'<h3[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    _SNIPPET = re.compile(r'<div[^>]+class="[^"]*compText[^"]*"[^>]*>(.*?)</div>', re.DOTALL)

    def build_url(self, query: str, page: int = 0) -> str:
        params = urllib.parse.urlencode({
            "p" : query,
            "b" : page * 10 + 1,
            "ei": "UTF-8",
        })
        return f"{self.BASE_URL}?{params}"

    def parse(self, html: str, engine_name: str) -> List[SearchResult]:
        results = []
        rank = 1
        for m in self._RESULT.finditer(html):
            block     = m.group(1)
            title_m   = self._TITLE.search(block)
            snippet_m = self._SNIPPET.search(block)

            if not title_m:
                continue

            # Yahoo sometimes wraps URLs in redirects
            raw_url = title_m.group(1)
            url     = urllib.parse.unquote(raw_url.split("RU=")[-1].split("/RK=")[0])
            if not url.startswith("http"):
                url = raw_url

            title   = _clean(title_m.group(2))
            snippet = _clean(snippet_m.group(1)) if snippet_m else ""

            results.append(SearchResult(engine_name, rank, title, url, snippet))
            rank += 1

        return results


# ─────────────────────────────────────────────
#  Engine registry
# ─────────────────────────────────────────────

ENGINES = {
    "google" : GoogleParser(),
    "bing"   : BingParser(),
    "yahoo"  : YahooParser(),
}


# ─────────────────────────────────────────────
#  Bot orchestrator
# ─────────────────────────────────────────────

def run_bot(
    query   : str,
    engines : List[str],
    pages   : int        = 1,
    delay   : float      = 2.0,
    verbose : bool       = False,
) -> SearchReport:
    """
    Execute the search across all requested engines and pages.
    Returns a consolidated SearchReport.
    """
    report = SearchReport(query=query, engines=engines)

    for engine_key in engines:
        parser = ENGINES[engine_key]
        print(f"  [*] Querying {parser.NAME} …")

        for page in range(pages):
            url = parser.build_url(query, page)
            if verbose:
                print(f"      → {url}")

            try:
                html    = _get(url)
                results = parser.parse(html, parser.NAME)
                for r in results:
                    r.rank += page * 10      # adjust rank for pagination
                    report.add(r)
                print(f"      ✓ Page {page + 1}: {len(results)} results")
            except Exception as exc:
                print(f"      ✗ Page {page + 1} failed: {exc}", file=sys.stderr)

            # Polite delay between requests
            if page < pages - 1:
                time.sleep(delay + random.uniform(0, 1))

        # Delay between engines
        time.sleep(delay)

    return report


# ─────────────────────────────────────────────
#  Report display
# ─────────────────────────────────────────────

C = {
    "reset"  : "\033[0m",
    "bold"   : "\033[1m",
    "green"  : "\033[92m",
    "yellow" : "\033[93m",
    "cyan"   : "\033[96m",
    "blue"   : "\033[94m",
    "red"    : "\033[91m",
    "dim"    : "\033[2m",
}

ENGINE_COLORS = {
    "Google" : "\033[94m",   # blue
    "Bing"   : "\033[92m",   # green
    "Yahoo"  : "\033[93m",   # yellow
}


def _c(key: str, text: str) -> str:
    return f"{C[key]}{text}{C['reset']}"


def print_report(report: SearchReport, dedup: bool = False) -> None:
    results = report.results
    if dedup:
        seen, filtered = set(), []
        for r in results:
            if r.url not in seen:
                seen.add(r.url)
                filtered.append(r)
        results = filtered

    print()
    print(_c("bold", "=" * 65))
    print(_c("cyan",  "  SEARCH BOT RESULTS"))
    print(f"  {_c('bold', 'Query')}   : {report.query}")
    print(f"  {_c('bold', 'Engines')} : {', '.join(report.engines)}")
    print(f"  {_c('bold', 'Time')}    : {report.timestamp}")
    print(f"  {_c('bold', 'Total')}   : {len(results)} results")
    print(_c("bold", "=" * 65))

    current_engine = None
    for r in results:
        if r.engine != current_engine:
            current_engine = r.engine
            color = ENGINE_COLORS.get(r.engine, C["cyan"])
            print(f"\n  {color}{_c('bold', f'── {r.engine} ──')}{C['reset']}\n")

        print(f"  {_c('dim', f'[{r.rank:02d}]')} {_c('bold', r.title)}")
        print(f"       {_c('green', r.url)}")
        if r.snippet:
            snippet = r.snippet[:120] + "…" if len(r.snippet) > 120 else r.snippet
            print(f"       {_c('dim', snippet)}")
        print()

    print(_c("bold", "=" * 65))

    # Unique URL list
    print(f"\n  {_c('cyan', 'Unique URLs found:')}")
    for url in report.unique_urls():
        print(f"    • {url}")
    print()


# ─────────────────────────────────────────────
#  Dork helper (common OSINT search operators)
# ─────────────────────────────────────────────

DORK_TEMPLATES: Dict[str, str] = {
    "site_recon"   : 'site:{target}',
    "subdomains"   : 'site:*.{target}',
    "login_pages"  : 'site:{target} inurl:login OR inurl:admin OR inurl:portal',
    "exposed_files": 'site:{target} filetype:pdf OR filetype:doc OR filetype:xls',
    "sql_errors"   : 'site:{target} "sql syntax" OR "mysql_fetch" OR "ORA-"',
    "open_dirs"    : 'intitle:"index of" site:{target}',
    "config_files" : 'site:{target} ext:env OR ext:config OR ext:bak',
    "emails"       : '"@{target}" email',
    "linkedin_emp" : 'site:linkedin.com/in "{target}"',
}


def list_dorks(target: Optional[str] = None) -> None:
    print("\n  Available Google Dork Templates:\n")
    for name, template in DORK_TEMPLATES.items():
        query = template.format(target=target) if target else template
        print(f"  {_c('yellow', name.ljust(16))} → {query}")
    print()


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Multi-engine search bot: queries Google, Bing & Yahoo "
            "and aggregates results.\n"
            "Supports Google Dorks for OSINT / security research."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search across all 3 engines
  python project2_search_bot.py --query "site:example.com"

  # Bing + Yahoo only, 2 pages each
  python project2_search_bot.py --query "python security" --engines bing yahoo --pages 2

  # Use a dork template
  python project2_search_bot.py --dork site_recon --target example.com

  # Save results to JSON, remove duplicates
  python project2_search_bot.py --query "admin panel" --output results.json --dedup

  # List available dork templates
  python project2_search_bot.py --list-dorks --target example.com
        """,
    )
    q_group = p.add_mutually_exclusive_group(required=True)
    q_group.add_argument("--query",      help="Raw search query (supports dork syntax)")
    q_group.add_argument("--dork",       choices=list(DORK_TEMPLATES.keys()),
                         help="Use a preset dork template (requires --target)")
    q_group.add_argument("--list-dorks", action="store_true",
                         help="Print available dork templates and exit")

    p.add_argument("--target",   help="Domain / company name for dork substitution")
    p.add_argument("--engines",  nargs="+", default=["google", "bing", "yahoo"],
                   choices=list(ENGINES.keys()), help="Engines to query (default: all)")
    p.add_argument("--pages",    type=int, default=1,
                   help="Number of result pages per engine (default: 1)")
    p.add_argument("--delay",    type=float, default=2.0,
                   help="Base delay (seconds) between requests (default: 2.0)")
    p.add_argument("--output",   help="JSON output filename (default: osint_<query>_<timestamp>.json)")
    p.add_argument("--dedup",    action="store_true",
                   help="Remove duplicate URLs from display")
    p.add_argument("--verbose",  action="store_true",
                   help="Print each request URL")
    p.add_argument("--no-color", action="store_true",
                   help="Disable ANSI colors")
    return p.parse_args()


def main() -> None:
    args = build_args()

    if args.no_color:
        for k in C:
            C[k] = ""
        for k in ENGINE_COLORS:
            ENGINE_COLORS[k] = ""

    # ── List dorks mode ───────────────────────────────
    if args.list_dorks:
        list_dorks(args.target)
        return

    # ── Resolve query ──────────────────────────────────
    if args.dork:
        if not args.target:
            print("[!] --dork requires --target", file=sys.stderr)
            sys.exit(1)
        query = DORK_TEMPLATES[args.dork].format(target=args.target)
        print(f"[*] Using dork: {query}")
    else:
        query = args.query

    # ── Run bot ───────────────────────────────────────
    print(f"\n[*] Starting search bot")
    print(f"[*] Query   : {query}")
    print(f"[*] Engines : {', '.join(args.engines)}")
    print(f"[*] Pages   : {args.pages}\n")

    report = run_bot(
        query   = query,
        engines = args.engines,
        pages   = args.pages,
        delay   = args.delay,
        verbose = args.verbose,
    )

    # ── Display ───────────────────────────────────────
    print_report(report, dedup=args.dedup)

    # ── Save ──────────────────────────────────────────
    # Sanitise query into a safe filename fragment (max 40 chars)
    safe_query = re.sub(r"[^a-zA-Z0-9]+", "_", report.query).strip("_")[:40]
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = args.output or f"osint_{safe_query}_{timestamp}.json"
    txt_file  = json_file.replace(".json", ".txt")

    # JSON — machine-readable full dump
    data = {
        "query"       : report.query,
        "engines"     : report.engines,
        "timestamp"   : report.timestamp,
        "total"       : len(report.results),
        "unique_urls" : report.unique_urls(),
        "results"     : [asdict(r) for r in report.results],
    }
    with open(json_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"[+] JSON report saved  → {json_file}")

    # TXT — human-readable summary
    with open(txt_file, "w", encoding="utf-8") as fh:
        fh.write("OSINT Search Bot Report\n")
        fh.write("=" * 65 + "\n")
        fh.write(f"Query     : {report.query}\n")
        fh.write(f"Engines   : {', '.join(report.engines)}\n")
        fh.write(f"Timestamp : {report.timestamp}\n")
        fh.write(f"Total     : {len(report.results)} results\n")
        fh.write("=" * 65 + "\n\n")

        current_engine = None
        for r in report.results:
            if r.engine != current_engine:
                current_engine = r.engine
                fh.write(f"\n── {r.engine} ──\n\n")
            fh.write(f"  [{r.rank:02d}] {r.title}\n")
            fh.write(f"       {r.url}\n")
            if r.snippet:
                snippet = r.snippet[:120] + "…" if len(r.snippet) > 120 else r.snippet
                fh.write(f"       {snippet}\n")
            fh.write("\n")

        fh.write("\n" + "=" * 65 + "\n")
        fh.write("Unique URLs\n")
        fh.write("=" * 65 + "\n")
        for url in report.unique_urls():
            fh.write(f"  • {url}\n")

    print(f"[+] TXT summary saved  → {txt_file}\n")


if __name__ == "__main__":
    main()