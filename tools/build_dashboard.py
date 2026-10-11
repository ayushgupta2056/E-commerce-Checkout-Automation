"""Build the static QA results dashboard published to GitHub Pages.

Everything on the page comes from the files produced by a real pytest run:
reports/junit.xml, reports/report.html, reports/test_run.log and the Playwright
artifacts in test-results/. Run metadata (time, commit, run link) comes from the
GitHub Actions environment, or is marked as a local run.

Usage:
    python tools/build_dashboard.py --out site [--history previous/history.json]
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
ARTIFACTS_DIR = PROJECT_ROOT / "test-results"
CATEGORY_LABELS = {"ui": "UI", "api": "API", "integration": "Integration"}
NEGATIVE_WORDS = ("invalid", "negative", "empty", "error", "declined", "out_of_stock", "no_results", "cannot", "rejected")
HISTORY_LIMIT = 30


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def run_metadata() -> dict:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    sha = os.environ.get("GITHUB_SHA", "")
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "GitHub Actions" if run_id else "Local run",
        "repository": repository,
        "run_id": run_id,
        "run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
        "run_url": f"{server}/{repository}/actions/runs/{run_id}" if run_id else "",
        "workflow_url": f"{server}/{repository}/actions/workflows/qa-tests.yml" if repository else "",
        "event": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "branch": os.environ.get("GITHUB_REF_NAME", ""),
        "sha": sha,
        "source_url": f"{server}/{repository}/blob/{sha}" if repository and sha else "",
        "target": os.environ.get("TARGET_BASE_URL", "Local FastAPI app started by conftest.py (http://127.0.0.1:5000)"),
        "runner": os.environ.get("RUNNER_OS", os.name),
    }


def test_line_numbers(file_path: Path) -> dict[str, int]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {}
    return {node.name: node.lineno for node in tree.body if isinstance(node, ast.FunctionDef)}


def parse_junit(junit_path: Path) -> tuple[dict, list[dict]]:
    root = ET.parse(junit_path).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    started = suite.get("timestamp", "")
    tests = []
    line_cache: dict[Path, dict[str, int]] = {}

    for case in suite.iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        base_name = name.split("[")[0]
        parts = classname.split(".")
        category = CATEGORY_LABELS.get(parts[1], "Other") if len(parts) > 1 else "Other"
        file_path = Path(*parts).with_suffix(".py")
        if file_path not in line_cache:
            line_cache[file_path] = test_line_numbers(PROJECT_ROOT / file_path)

        status, detail = "passed", ""
        for tag in ("failure", "error", "skipped"):
            element = case.find(tag)
            if element is None:
                continue
            message = element.get("message", "")
            text = (element.text or "").strip()
            if tag == "skipped" and element.get("type") == "pytest.xfail":
                status = "xfailed"
            elif tag == "skipped":
                status = "skipped"
            else:
                status = "failed" if tag == "failure" else "error"
            detail = message if status in ("xfailed", "skipped") else (text or message)
            break

        tests.append(
            {
                "name": name,
                "base_name": base_name,
                "file": file_path.as_posix(),
                "line": line_cache[file_path].get(base_name),
                "category": category,
                "negative": any(word in base_name for word in NEGATIVE_WORDS) or status == "xfailed",
                "status": status,
                "duration": float(case.get("time", 0) or 0),
                "detail": detail,
                "evidence": [],
            }
        )
    return {"started": started}, tests


def attach_evidence(tests: list[dict], out_dir: Path) -> None:
    if not ARTIFACTS_DIR.exists():
        return
    folders = [folder for folder in ARTIFACTS_DIR.iterdir() if folder.is_dir()]
    evidence_root = out_dir / "evidence"
    for test in tests:
        test_slug = slug(test["name"])
        matches = [folder for folder in folders if folder.name.endswith(test_slug)]
        for folder in matches:
            target = evidence_root / folder.name
            shutil.copytree(folder, target, dirs_exist_ok=True)
            for file in sorted(target.iterdir()):
                relative = file.relative_to(out_dir).as_posix()
                if file.suffix == ".zip":
                    kind = "trace"
                elif file.suffix == ".webm":
                    kind = "video"
                elif file.suffix == ".png":
                    kind = "screenshot"
                else:
                    continue
                test["evidence"].append({"kind": kind, "path": relative})

    for screenshot in sorted((REPORTS_DIR / "screenshots").glob("*.png")):
        target = evidence_root / "failure-screenshots" / screenshot.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(screenshot, target)
        for test in tests:
            if screenshot.stem == test["name"].replace("/", "_").replace("\\", "_"):
                test["evidence"].append({"kind": "failure screenshot", "path": target.relative_to(out_dir).as_posix()})


def summarise(tests: list[dict]) -> dict:
    counts = {status: sum(1 for test in tests if test["status"] == status) for status in ("passed", "failed", "error", "skipped", "xfailed")}
    counts["total"] = len(tests)
    counts["duration"] = round(sum(test["duration"] for test in tests), 1)
    by_category = {}
    for test in tests:
        bucket = by_category.setdefault(test["category"], {"total": 0, "passed": 0, "xfailed": 0})
        bucket["total"] += 1
        bucket["passed"] += test["status"] == "passed"
        bucket["xfailed"] += test["status"] == "xfailed"
    counts["categories"] = by_category
    counts["negative"] = sum(1 for test in tests if test["negative"])
    return counts


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def evidence_links(test: dict, meta: dict) -> str:
    links = []
    pages_base = os.environ.get("PAGES_BASE_URL", "").rstrip("/")
    for item in test["evidence"]:
        if item["kind"] == "trace":
            if pages_base:
                viewer = f"https://trace.playwright.dev/?trace={pages_base}/{item['path']}"
                links.append(f'<a href="{esc(viewer)}" target="_blank" rel="noopener">trace viewer</a>')
            links.append(f'<a href="{esc(item["path"])}">trace.zip</a>')
        else:
            links.append(f'<a href="{esc(item["path"])}" target="_blank" rel="noopener">{esc(item["kind"])}</a>')
    if meta["source_url"] and test["line"]:
        code_url = f'{meta["source_url"]}/{test["file"]}#L{test["line"]}'
        links.append(f'<a href="{esc(code_url)}" target="_blank" rel="noopener">test code</a>')
    return " · ".join(links) or "—"


def render(meta: dict, junit_meta: dict, tests: list[dict], summary: dict, history: list[dict]) -> str:
    status_order = {"failed": 0, "error": 1, "xfailed": 2, "skipped": 3, "passed": 4}
    category_order = {"UI": 0, "API": 1, "Integration": 2, "Other": 3}
    rows = []
    for test in sorted(tests, key=lambda t: (category_order.get(t["category"], 9), status_order[t["status"]], t["name"])):
        tags = f'<span class="tag">{esc(test["category"])}</span>'
        if test["negative"]:
            tags += '<span class="tag neg">negative</span>'
        detail = f'<details><summary>details</summary><pre>{esc(test["detail"])}</pre></details>' if test["detail"] else ""
        rows.append(
            f'<tr data-status="{test["status"]}" data-category="{esc(test["category"])}">'
            f'<td><span class="pill {test["status"]}">{esc(test["status"].upper())}</span></td>'
            f'<td><code>{esc(test["name"])}</code><div class="sub">{esc(test["file"])}</div>{detail}</td>'
            f"<td>{tags}</td>"
            f'<td class="num">{test["duration"]:.2f}s</td>'
            f'<td class="links">{evidence_links(test, meta)}</td></tr>'
        )

    category_cards = "".join(
        f'<div class="card"><div class="label">{esc(name)} tests</div><div class="value">{data["passed"]}/{data["total"] - data["xfailed"]}</div><div class="sub">passed{(" + " + str(data["xfailed"]) + " known-defect checks") if data["xfailed"] else ""}</div></div>'
        for name, data in sorted(summary["categories"].items(), key=lambda item: category_order.get(item[0], 9))
    )
    history_rows = "".join(
        f'<tr><td>{esc(run["generated_at"])}</td><td>{esc(run["source"])} {esc(run.get("event", ""))}</td>'
        f'<td>{esc(run["passed"])}/{esc(run["total"])} passed, {esc(run["failed"])} failed, {esc(run["xfailed"])} xfailed</td>'
        f'<td><code>{esc(run.get("sha", "")[:7])}</code></td>'
        f'<td>{"<a href=" + chr(34) + esc(run["run_url"]) + chr(34) + ">run</a>" if run.get("run_url") else "—"}</td></tr>'
        for run in reversed(history)
    )
    run_link = f'<a href="{esc(meta["run_url"])}">GitHub Actions run #{esc(meta["run_number"])}</a>' if meta["run_url"] else "Local run (not from CI)"
    trigger = (
        f'<a class="button" href="{esc(meta["workflow_url"])}">Run tests again (repository owner)</a>'
        if meta["workflow_url"]
        else ""
    )
    overall = "failed" if summary["failed"] or summary["error"] else "passed"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QA Automation Results</title>
<style>
:root {{ --bg:#f6f7f9; --panel:#fff; --text:#1c2430; --muted:#5f6b7a; --line:#e2e6ec; --accent:#0b5cad;
  --pass:#1f7a3d; --pass-bg:#e5f4ea; --fail:#b42318; --fail-bg:#fde8e7; --warn:#8a5a00; --warn-bg:#fff2d6; --skip:#4b5563; --skip-bg:#eceff3; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#11151b; --panel:#1a2029; --text:#e6e9ee; --muted:#9aa5b4; --line:#2b3340; --accent:#6aa9ff;
  --pass:#6fd08c; --pass-bg:#173322; --fail:#ff8a80; --fail-bg:#3a1a19; --warn:#f3c969; --warn-bg:#3a2e12; --skip:#b4bdc9; --skip-bg:#262d37; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
a {{ color:var(--accent); }}
.wrap {{ max-width:1180px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ margin:0 0 4px; font-size:26px; }} h2 {{ font-size:18px; margin:32px 0 12px; }}
.lede {{ color:var(--muted); margin:0 0 20px; max-width:760px; }}
.meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:4px 24px; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px 16px; font-size:14px; }}
.meta b {{ color:var(--muted); font-weight:600; margin-right:6px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-top:16px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; }}
.card .label {{ color:var(--muted); font-size:13px; }} .card .value {{ font-size:28px; font-weight:700; font-variant-numeric:tabular-nums; }}
.card.passed .value {{ color:var(--pass); }} .card.failed .value {{ color:var(--fail); }} .card.xfailed .value {{ color:var(--warn); }}
.sub {{ color:var(--muted); font-size:12px; }}
.banner {{ border-radius:10px; padding:12px 16px; margin:16px 0 0; font-weight:600; }}
.banner.passed {{ background:var(--pass-bg); color:var(--pass); }} .banner.failed {{ background:var(--fail-bg); color:var(--fail); }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 12px; }}
.toolbar button, .button {{ border:1px solid var(--line); background:var(--panel); color:var(--text); border-radius:8px; padding:6px 12px; cursor:pointer; font:inherit; font-size:14px; text-decoration:none; display:inline-block; }}
.toolbar button.on {{ border-color:var(--accent); color:var(--accent); font-weight:600; }}
.table-wrap {{ overflow-x:auto; background:var(--panel); border:1px solid var(--line); border-radius:10px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; font-size:13px; }}
tr:last-child td {{ border-bottom:none; }}
td.num {{ font-variant-numeric:tabular-nums; white-space:nowrap; }} td.links {{ min-width:180px; }}
code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:13px; word-break:break-word; }}
pre {{ white-space:pre-wrap; font-size:12px; max-height:260px; overflow:auto; background:var(--bg); padding:8px; border-radius:6px; }}
.pill {{ display:inline-block; border-radius:999px; padding:2px 9px; font-size:12px; font-weight:700; }}
.pill.passed {{ background:var(--pass-bg); color:var(--pass); }} .pill.failed, .pill.error {{ background:var(--fail-bg); color:var(--fail); }}
.pill.xfailed {{ background:var(--warn-bg); color:var(--warn); }} .pill.skipped {{ background:var(--skip-bg); color:var(--skip); }}
.tag {{ display:inline-block; border:1px solid var(--line); border-radius:6px; padding:0 6px; font-size:12px; margin:0 4px 4px 0; }}
.tag.neg {{ border-color:var(--warn); color:var(--warn); }}
.links-row {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
.note {{ color:var(--muted); font-size:13px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>E-Commerce Checkout Automation — Test Results</h1>
  <p class="lede">Results of the Playwright + Pytest framework testing the QA Shop FastAPI application across UI, REST API and SQLite database layers.
  This page is generated from the JUnit XML and Playwright artifacts of the run listed below; nothing on it is entered by hand.</p>

  <div class="meta">
    <div><b>Generated</b>{esc(meta["generated_at"])}</div>
    <div><b>Source</b>{run_link}</div>
    <div><b>Trigger</b>{esc(meta["event"])}{(" on " + esc(meta["branch"])) if meta["branch"] else ""}</div>
    <div><b>Commit</b><code>{esc(meta["sha"][:7] or "n/a")}</code></div>
    <div><b>pytest started</b>{esc(junit_meta["started"] or "n/a")}</div>
    <div><b>Target</b>{esc(meta["target"])}</div>
  </div>

  <div class="banner {overall}">{"All executed tests passed" if overall == "passed" else "Some tests failed"} — {summary["passed"]} passed, {summary["failed"] + summary["error"]} failed, {summary["xfailed"]} known defects (xfail), {summary["skipped"]} skipped, {summary["duration"]}s total.</div>

  <div class="cards">
    <div class="card"><div class="label">Total tests</div><div class="value">{summary["total"]}</div></div>
    <div class="card passed"><div class="label">Passed</div><div class="value">{summary["passed"]}</div></div>
    <div class="card failed"><div class="label">Failed / error</div><div class="value">{summary["failed"] + summary["error"]}</div></div>
    <div class="card xfailed"><div class="label">Known defects (xfail)</div><div class="value">{summary["xfailed"]}</div></div>
    <div class="card"><div class="label">Skipped</div><div class="value">{summary["skipped"]}</div></div>
    <div class="card"><div class="label">Negative scenarios</div><div class="value">{summary["negative"]}</div></div>
    {category_cards}
  </div>

  <div class="links-row">
    <a class="button" href="report.html">Full pytest-html report</a>
    <a class="button" href="junit.xml">JUnit XML</a>
    <a class="button" href="test_run.log">Execution log</a>
    {trigger}
  </div>
  <p class="note">XFAIL = a test that asserts the correct behaviour for an open defect (docs/jira/DEFECT-004 to 006). It is expected to fail until the defect is fixed.
  Trace viewer links open the recorded Playwright trace (DOM snapshots, network, console) in trace.playwright.dev.</p>

  <h2>Test cases</h2>
  <div class="toolbar" id="filters">
    <button class="on" data-filter="all">All</button>
    <button data-filter="UI">UI</button><button data-filter="API">API</button><button data-filter="Integration">Integration</button>
    <button data-filter="failed">Failed</button><button data-filter="xfailed">Known defects</button>
  </div>
  <div class="table-wrap"><table>
    <thead><tr><th>Status</th><th>Test</th><th>Type</th><th>Time</th><th>Evidence</th></tr></thead>
    <tbody id="tests">{"".join(rows)}</tbody>
  </table></div>

  <h2>Run history</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Generated</th><th>Source</th><th>Result</th><th>Commit</th><th>Link</th></tr></thead>
    <tbody>{history_rows}</tbody>
  </table></div>
</div>
<script>
document.getElementById("filters").addEventListener("click", function (event) {{
  var button = event.target.closest("button"); if (!button) return;
  var filter = button.dataset.filter;
  document.querySelectorAll("#filters button").forEach(function (b) {{ b.classList.toggle("on", b === button); }});
  document.querySelectorAll("#tests tr").forEach(function (row) {{
    var show = filter === "all" || row.dataset.category === filter || row.dataset.status === filter ||
      (filter === "failed" && row.dataset.status === "error");
    row.style.display = show ? "" : "none";
  }});
}});
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="site")
    parser.add_argument("--history", default="")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    meta = run_metadata()
    junit_meta, tests = parse_junit(REPORTS_DIR / "junit.xml")
    attach_evidence(tests, out_dir)
    summary = summarise(tests)

    history = []
    if args.history and Path(args.history).exists():
        history = json.loads(Path(args.history).read_text(encoding="utf-8"))
    history.append(
        {
            "generated_at": meta["generated_at"],
            "source": meta["source"],
            "event": meta["event"],
            "sha": meta["sha"],
            "run_url": meta["run_url"],
            **{key: summary[key] for key in ("total", "passed", "failed", "error", "skipped", "xfailed")},
        }
    )
    history = history[-HISTORY_LIMIT:]

    for name in ("report.html", "junit.xml", "test_run.log"):
        if (REPORTS_DIR / name).exists():
            shutil.copy2(REPORTS_DIR / name, out_dir / name)
    (out_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps({"meta": meta, "summary": summary, "tests": tests}, indent=2), encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    (out_dir / "index.html").write_text(render(meta, junit_meta, tests, summary, history), encoding="utf-8")
    print(f"Dashboard written to {out_dir} ({summary['passed']}/{summary['total']} passed)")


if __name__ == "__main__":
    main()
