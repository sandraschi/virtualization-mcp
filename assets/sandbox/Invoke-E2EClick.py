#!/usr/bin/env python3
"""In-sandbox E2E webapp clickthrough (CUA via UIA, no OCR).

Runs INSIDE the Windows Sandbox after the naked-test harness has the
app stack up. Generic across repos: no per-repo config. Adapts the
host-side scripts/cua-webapp-test.py plan to sandbox constraints:

  - No tesseract in the sandbox, so the "Connected" badge check and the
    fail-scan use UIA text matching instead of OCR screenshots.
  - Screenshots only need PIL (pywinauto capture_as_image).
  - Browser is Edge by executable path (no http-association dialog).

Needs: pywinauto, pillow (run under `uv run --with ...`).

Exit 0 + E2E.json pass=true when at least one page was clicked and no
fail keywords appeared. Writes e2e-<slug>.png per page into the job dir.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CONNECTED_KEYWORDS = ("connected", "system online", "online", "ready")
FAIL_KEYWORDS = (
    "404",
    "not found",
    "internal server error",
    "failed to fetch",
    "cannot connect",
    "connection refused",
    "something went wrong",
)
MAX_PAGES = 12


def log(msg):
    print(f"  [e2e-click] {msg}", flush=True)


def find_edge_window_for_url(port):
    """Top-level Edge window whose address bar shows our frontend port."""
    from pywinauto import Desktop

    needle = f"127.0.0.1:{port}"
    for w in Desktop(backend="uia").windows():
        try:
            if not w.is_visible():
                continue
            for edit in w.descendants(control_type="Edit"):
                try:
                    if needle in (edit.window_text() or ""):
                        return w
                except Exception:
                    pass
        except Exception:
            pass
    return None


def window_texts(win):
    texts = []
    try:
        for el in win.descendants():
            try:
                t = el.window_text()
                if t:
                    texts.append(t)
            except Exception:
                pass
    except Exception:
        pass
    return texts


def main():
    ap = argparse.ArgumentParser(description="In-sandbox E2E webapp clickthrough")
    ap.add_argument("--frontend-url", required=True)
    ap.add_argument("--job-dir", required=True)
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()

    job_dir = Path(args.job_dir)
    m = re.search(r":(\d+)", args.frontend_url or "")
    port = m.group(1) if m else ""
    result = {
        "frontend_url": args.frontend_url,
        "pass": False,
        "connected_seen": False,
        "pages": [],
        "failures": [],
    }

    def done(ok):
        result["pass"] = ok
        try:
            (job_dir / "E2E.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        except OSError as e:
            log(f"E2E.json write failed: {e}")
        return 0 if ok else 1

    try:
        from pywinauto import Desktop  # noqa: F401
    except Exception as e:
        result["failures"].append(f"pywinauto import failed: {e}")
        log(f"pywinauto import failed: {e}")
        return done(False)

    # Open Edge by exe path (no association dialog on fresh sandboxes).
    try:
        subprocess.Popen([EDGE_EXE, args.frontend_url])
        log(f"Edge opening {args.frontend_url}")
    except Exception as e:
        result["failures"].append(f"edge launch failed: {e}")
        return done(False)

    deadline = time.time() + args.timeout
    win = None
    while time.time() < deadline and win is None:
        win = find_edge_window_for_url(port) if port else None
        if win is None:
            time.sleep(3)
    if win is None:
        result["failures"].append("no Edge window showing the frontend URL")
        return done(False)
    log("Edge window found")

    try:
        win.maximize()
        time.sleep(1)
        win.set_focus()
        time.sleep(2)
    except Exception:
        pass

    Texts = " ".join(window_texts(win)).lower()
    if any(k in Texts for k in CONNECTED_KEYWORDS):
        result["connected_seen"] = True
        log("connected/ready text seen")
    else:
        log("no connected badge text (best-effort, continuing)")

    # Sidebar walk: unique visible hyperlinks, in order.
    seen = []
    try:
        for el in win.descendants(control_type="Hyperlink"):
            try:
                label = (el.window_text() or "").strip()
                if label and label.lower() not in [s.lower() for s in seen]:
                    seen.append(label)
            except Exception:
                pass
    except Exception as e:
        result["failures"].append(f"hyperlink scan failed: {e}")
        return done(False)
    log(f"{len(seen)} sidebar links: {seen[:MAX_PAGES]}")

    clicked = 0
    for label in seen[:MAX_PAGES]:
        try:
            targets = win.descendants(title=label, control_type="Hyperlink")
            if not targets:
                continue
            targets[0].click_input()
            time.sleep(2)
            slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "page"
            shot = job_dir / f"e2e-{clicked:02d}-{slug}.png"
            try:
                win.capture_as_image().save(str(shot))
            except Exception as e:
                result["failures"].append(f"screenshot failed on '{label}': {e}")
                continue
            page_text = " ".join(window_texts(win)).lower()
            bad = [k for k in FAIL_KEYWORDS if k in page_text]
            if bad:
                result["failures"].append(f"page '{label}' shows fail keywords: {bad}")
                log(f"page '{label}': FAIL keywords {bad}")
                continue
            result["pages"].append({"label": label, "screenshot": shot.name})
            clicked += 1
            log(f"page '{label}': ok ({shot.name})")
        except Exception as e:
            result["failures"].append(f"click failed on '{label}': {e}")

    if clicked == 0 and not result["failures"]:
        result["failures"].append("no pages could be clicked")
    return done(clicked > 0 and not result["failures"])


if __name__ == "__main__":
    sys.exit(main())
