# Recommended scan targets

A curated list of sites that are safe and legal to scan for testing, demos, or building a
training dataset for the ML false-positive classifier (see [`ML/`](../../ML/)).

## Category 1: Intentionally vulnerable applications
Contain real, known vulnerabilities - useful for exercising every scan type.

| Site | Notes |
|---|---|
| http://testphp.vulnweb.com | SQL injection, XSS, file inclusion |
| http://www.itsecgames.com | bWAPP - 100+ vulnerabilities |
| http://zero.webappsecurity.com | Banking app vulnerabilities |
| https://juice-shop.herokuapp.com | OWASP Juice Shop |
| http://demo.testfire.net | IBM testfire |
| https://public-firing-range.appspot.com | Google XSS testing ground |
| http://testhtml5.vulnweb.com | HTML5/modern vulnerabilities |
| http://testasp.vulnweb.com | ASP.NET vulnerabilities |

## Category 2: Production sites with strong security
Good for observing what a clean scan looks like and calibrating false-positive rates. Passive
scanning only - do not run active/intrusive scans against sites you don't own or have permission
to test.

`github.com`, `stackoverflow.com`, `wikipedia.org`, `cloudflare.com`, `npmjs.com`, `docker.com`

## Category 3: Public test APIs

`api.github.com`, `jsonplaceholder.typicode.com`, `reqres.in`

## Category 4: General test/demo sites

`example.com`, `httpbin.org`, `www.webscantest.com`

## Legal & ethical notes

- Intentionally-vulnerable apps (Category 1) are explicitly built to be scanned, including
  actively.
- Everything else: passive/non-intrusive scanning only, unless you own the target or have
  explicit written authorization for active scanning.
- Respect `robots.txt` and rate limits.
- Never scan a third party's production infrastructure without their permission - this
  repository does not ship any scan data collected against real third-party targets, precisely
  for this reason.
