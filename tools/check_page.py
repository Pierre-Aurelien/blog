"""Screenshot a rendered page and check it, as the definition of done asks.

    python tools/check_page.py posts/<slug>            # after `quarto render`
    python tools/check_page.py legacy/2026-09-jepa-lejepa.html --no-checks

Serves _site/ locally, opens the page in light mode, dark mode, and at 390 px
in both, with every fold open, and fails if:
  - the page logs a JavaScript error;
  - the page scrolls horizontally at phone width;
  - an SVG label runs outside its SVG;
  - a canvas is blank, or a slider does not change its figure;
  - a formula failed to typeset;
  - the colour tokens do not switch between light and dark, a data-theme
    attribute does not override the system theme, or widgets do not redraw
    when the theme changes.
Screenshots go to screenshots/<page>/ (gitignored).

Needs requirements-dev.txt (Playwright). It drives the Chrome installed on the
machine if there is one, otherwise run `playwright install chromium` once.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

VIEWS = [
    # name, width, height, colour scheme
    ("light", 1280, 900, "light"),
    ("dark", 1280, 900, "dark"),
    ("phone-light", 390, 844, "light"),
    ("phone-dark", 390, 844, "dark"),
]

TOKENS = {"light": "#fdfcfa", "dark": "#12161d"}  # --bg in theme/tokens.scss

# Run in the page. Each returns a list of problems (strings).
JS_WAIT = """async () => {
  if (document.fonts && document.fonts.ready) await document.fonts.ready;
  if (window.MathJax && MathJax.startup && MathJax.startup.promise) await MathJax.startup.promise;
  for (const b of document.querySelectorAll('[data-fold="open"], #unfoldAll')) { b.click(); break; }
  await new Promise(r => setTimeout(r, 300));
}"""

JS_HSCROLL = """() => {
  const W = document.documentElement.clientWidth, out = [];
  if (document.documentElement.scrollWidth <= W + 1) return out;
  out.push(`page is ${document.documentElement.scrollWidth}px wide in a ${W}px viewport`);
  const scrolls = el => { for (let p = el.parentElement; p; p = p.parentElement) {
    const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') return true; } return false; };
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > W + 1 && !scrolls(el)) {
      const id = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
      out.push(`  overflows: ${id} (right edge at ${Math.round(r.right)}px)`);
      if (out.length > 6) break;
    }
  }
  return out;
}"""

JS_SVG_TEXT = """() => {
  const out = [];
  for (const svg of document.querySelectorAll('svg')) {
    if (svg.closest('mjx-container') || svg.closest('.bi') || svg.getAttribute('aria-hidden') === 'true') continue;
    const vb = svg.viewBox && svg.viewBox.baseVal;
    const box = vb && vb.width ? vb : { x: 0, y: 0, width: svg.width.baseVal.value, height: svg.height.baseVal.value };
    if (!box.width) continue;
    for (const t of svg.querySelectorAll('text')) {
      let b; try { b = t.getBBox(); } catch (e) { continue; }
      if (!b.width) continue;
      if (b.x < box.x - 0.5 || b.y < box.y - 0.5 || b.x + b.width > box.x + box.width + 0.5 || b.y + b.height > box.y + box.height + 0.5) {
        out.push(`SVG text "${t.textContent.trim().slice(0, 40)}" runs outside its SVG (${Math.round(b.x)}..${Math.round(b.x + b.width)} of ${Math.round(box.x)}..${Math.round(box.x + box.width)})`);
      }
    }
  }
  return out;
}"""

JS_CANVASES = """() => {
  const out = [];
  for (const cv of document.querySelectorAll('main canvas')) {
    const name = cv.id || 'a canvas';
    if (!cv.width || !cv.height) { out.push(`${name} has no size`); continue; }
    let ink = 0;
    try {
      const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
      for (let i = 3; i < d.length; i += 16) if (d[i] > 0) ink++;
    } catch (e) { out.push(`${name} cannot be read: ${e}`); continue; }
    if (!ink) out.push(`${name} is blank`);
  }
  return out;
}"""

JS_FIG_STATE = """(fig) => {
  const parts = [];
  for (const cv of fig.querySelectorAll('canvas')) parts.push(cv.toDataURL());
  for (const el of fig.querySelectorAll('.readout, svg')) parts.push(el.innerHTML);
  return parts.join('|');
}"""

JS_MATH = """() => {
  const out = [];
  const errors = document.querySelectorAll('mjx-merror, [data-mjx-error]');
  if (errors.length) out.push(`${errors.length} formula(s) failed to typeset, e.g. "${errors[0].getAttribute('data-mjx-error') || errors[0].textContent}"`);
  const raw = [...document.querySelectorAll('span.math')].filter(s => !s.querySelector('mjx-container'));
  if (raw.length) out.push(`${raw.length} formula(s) left untypeset, e.g. "${raw[0].textContent.slice(0, 40)}"`);
  return out;
}"""

JS_BG = """() => getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().toLowerCase()"""


def serve(directory: Path) -> tuple[socketserver.TCPServer, int]:
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def digest(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()


def check_sliders(page) -> list[str]:
    """Move every range input inside a figure; its figure must change."""
    problems = []
    for fig in page.query_selector_all("main .fig"):
        for slider in fig.query_selector_all('input[type="range"]'):
            name = slider.get_attribute("id") or slider.get_attribute("aria-label") or "a slider"
            before = digest(page.evaluate(JS_FIG_STATE, fig))
            lo, hi, value = (slider.get_attribute(a) for a in ("min", "max", "value"))
            target = lo if value != lo else hi
            slider.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); }", target)
            page.wait_for_timeout(150)
            after = digest(page.evaluate(JS_FIG_STATE, fig))
            if before == after:
                problems.append(f"slider #{name} does not change its figure")
            slider.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); }", value)
            page.wait_for_timeout(100)
        for button in fig.query_selector_all(".seg button"):
            before = digest(page.evaluate(JS_FIG_STATE, fig))
            button.click()
            page.wait_for_timeout(150)
            if digest(page.evaluate(JS_FIG_STATE, fig)) == before and button.get_attribute("aria-pressed") != "true":
                problems.append(f'preset "{button.inner_text()}" does nothing')
    return problems


def check_theme_override(page) -> list[str]:
    """In a dark system theme, data-theme="light" must win, and widgets must redraw."""
    problems = []
    canvases = lambda: page.evaluate("() => [...document.querySelectorAll('main canvas')].map(c => c.toDataURL()).join('|')")
    before = canvases()
    page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
    page.wait_for_timeout(250)
    if page.evaluate(JS_BG) != TOKENS["light"]:
        problems.append('data-theme="light" does not override the dark system theme')
    if before and canvases() == before:
        problems.append("widgets do not redraw when the theme changes")
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.wait_for_timeout(250)
    if page.evaluate(JS_BG) != TOKENS["dark"]:
        problems.append("removing data-theme does not return to the system theme")
    return problems


def launch(p):
    try:
        return p.chromium.launch(channel="chrome")
    except PlaywrightError:
        return p.chromium.launch()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", help="page path inside _site, e.g. posts/2026-10-slug or legacy/x.html")
    ap.add_argument("--site", default=str(ROOT / "_site"))
    ap.add_argument("--out", default=None, help="screenshot folder (default screenshots/<page>)")
    ap.add_argument("--no-checks", action="store_true", help="screenshots only")
    args = ap.parse_args()

    site = Path(args.site)
    rel = args.page.strip("/")
    if not rel.endswith(".html"):
        rel = rel + "/index.html"
    if not (site / rel).exists():
        print(f"{site / rel} not found: run `quarto render` first.")
        return 2
    out = Path(args.out) if args.out else ROOT / "screenshots" / Path(rel).with_suffix("").as_posix().replace("/index", "").replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)

    server, port = serve(site)
    url = f"http://127.0.0.1:{port}/{rel}"
    failures: list[str] = []
    with sync_playwright() as p:
        browser = launch(p)
        for name, width, height, scheme in VIEWS:
            ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme,
                                      device_scale_factor=2 if width < 600 else 1)
            page = ctx.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(f"JavaScript error: {e}"))
            page.on("console", lambda m: errors.append(f"console error: {m.text}") if m.type == "error" else None)
            page.goto(url, wait_until="networkidle")
            page.evaluate(JS_WAIT)
            problems = []
            if not args.no_checks:
                problems += errors
                if width < 600:
                    problems += page.evaluate(JS_HSCROLL)
                problems += page.evaluate(JS_SVG_TEXT)
                problems += page.evaluate(JS_CANVASES)
                problems += page.evaluate(JS_MATH)
                bg = page.evaluate(JS_BG)
                if bg != TOKENS[scheme]:
                    problems.append(f"--bg is {bg} in {scheme} mode, expected {TOKENS[scheme]}")
                if name == "light":
                    problems += check_sliders(page)
                if name == "dark":
                    problems += check_theme_override(page)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)
            shot = out / f"{name}.png"
            page.screenshot(path=str(shot), full_page=True)
            status = "ok" if not problems else f"{len(problems)} problem(s)"
            print(f"{name:12s} {width}x{height}  {status:14s} {shot.relative_to(ROOT) if shot.is_relative_to(ROOT) else shot}")
            for prob in problems:
                print(f"    - {prob}")
            failures += [f"{name}: {prob}" for prob in problems]
            ctx.close()
        browser.close()
    server.shutdown()
    if failures:
        print(f"\nFAILED: {len(failures)} problem(s).")
        return 1
    print("\nAll checks passed." if not args.no_checks else "\nScreenshots taken.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
