"""Offline and optional live evaluation for biomodel-agent."""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model_ir import validate_model_ir  # noqa: E402
from report_validation import validate_report_content  # noqa: E402
from simulate import simulate_model  # noqa: E402


def load_cases(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("cases file must contain a JSON array")
    return payload


def case_expected(case):
    return case.get("expected", {})


def check_common(case, ir, simulation, report_text=None):
    expected = case_expected(case)
    ir_validation = validate_model_ir(ir, for_simulation=True)
    var_names = {v.get("name") for v in ir.get("variables", []) if isinstance(v, dict)}
    expected_vars = set(expected.get("variables", []))
    checks = {
        "ir_valid": ir_validation["valid"],
        "model_type": ir.get("model_type") == expected.get("model_type", case.get("model_type")),
        "variables": expected_vars.issubset(var_names),
        "origin_mode": ir.get("origin", {}).get("mode") == expected.get("origin_mode"),
        "simulation_ok": simulation.get("status") == "ok",
        "run_metadata": bool(simulation.get("run_metadata")),
    }
    report_validation = None
    if report_text:
        report_validation = validate_report_content(report_text)
        checks["report_valid"] = report_validation["valid"]
        checks["report_coverage"] = (
            sum(report_validation["checks"].values()) / len(report_validation["checks"])
            if report_validation["checks"] else 0.0
        )
    required = ["ir_valid", "model_type", "variables", "origin_mode", "simulation_ok", "run_metadata"]
    if report_text:
        required.append("report_valid")
    passed = all(checks.get(key, False) for key in required)
    return {
        "passed": passed,
        "checks": checks,
        "errors": ir_validation["errors"],
        "warnings": ir_validation["warnings"] + (report_validation["warnings"] if report_validation else []),
        "report_validation": report_validation,
    }


def run_offline_case(case, base_tmp):
    case_id = case["id"]
    with tempfile.TemporaryDirectory(prefix=f"{case_id}_", dir=base_tmp) as tmp:
        result = simulate_model(case["ir"], output_dir=tmp, tag="eval")
        report_text = case.get("report_sample", "")
        checked = check_common(case, case["ir"], result, report_text)
        checked["case_id"] = case_id
        checked["name"] = case.get("name", case_id)
        checked["mode"] = "offline"
        checked["simulation_file"] = result.get("results_file")
        return checked


def _choose_latest(files):
    files = list(files)
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def run_live_case(case, client, model):
    from agent import run_agent
    from prompts import SYSTEM_PROMPT
    from tools import FUNCTIONS, TOOLS

    case_id = case["id"]
    with tempfile.TemporaryDirectory(prefix=f"live_{case_id}_") as tmp:
        old_cwd = os.getcwd()
        os.chdir(tmp)
        try:
            paper_path = Path(tmp) / "paper.txt"
            paper_path.write_text(case.get("paper_text", ""), encoding="utf-8")
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"请读取并处理这篇文献：{paper_path}。"
                        "如果给出完整模型，请复现；如果只有机制，请按假设驱动构建模型。"
                        "请保存 Model IR、完成模拟，并生成 Markdown 报告。"
                    ),
                },
            ]
            final_text = run_agent(client, model, messages, TOOLS, FUNCTIONS, verbose=False)
            ir_file = _choose_latest(Path("output").glob("model_ir_*.json"))
            if ir_file is None:
                return {
                    "case_id": case_id,
                    "name": case.get("name", case_id),
                    "mode": "live",
                    "passed": False,
                    "errors": ["agent did not save a Model IR"],
                    "warnings": [],
                    "checks": {},
                    "final_text": final_text,
                }
            ir = json.loads(ir_file.read_text(encoding="utf-8"))
            sim_file = _choose_latest(Path("output").glob("simulation_*.json"))
            simulation = {}
            if sim_file is not None:
                simulation = json.loads(sim_file.read_text(encoding="utf-8"))
                simulation["status"] = "ok"
            report_file = _choose_latest(Path("output/reports").glob("*.md"))
            report_text = report_file.read_text(encoding="utf-8") if report_file else ""
            checked = check_common(case, ir, simulation, report_text)
            checked.update({
                "case_id": case_id,
                "name": case.get("name", case_id),
                "mode": "live",
                "ir_file": str(ir_file),
                "simulation_file": str(sim_file) if sim_file else None,
                "report_file": str(report_file) if report_file else None,
                "final_text": final_text,
            })
            return checked
        finally:
            os.chdir(old_cwd)


def run_live(cases, case_filter=None):
    from main import LLM_PROVIDERS
    from openai import OpenAI

    provider = os.getenv("BIOMODEL_PROVIDER", "ustc").strip().lower()
    preset = LLM_PROVIDERS.get(provider)
    if preset is None:
        raise SystemExit(f"unsupported BIOMODEL_PROVIDER: {provider}")
    api_key = os.getenv(preset["api_key_env"])
    if not api_key:
        raise SystemExit(f"missing {preset['api_key_env']} for live evaluation")
    model = os.getenv("BIOMODEL_MODEL", preset["model"])
    base_url = os.getenv("BIOMODEL_BASE_URL", preset["base_url"])
    timeout = float(os.getenv("BIOMODEL_REQUEST_TIMEOUT", "120"))
    retries = int(os.getenv("BIOMODEL_MAX_RETRIES", "2"))
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=retries)

    selected = [c for c in cases if not case_filter or c["id"] == case_filter]
    results = []
    for case in selected:
        try:
            results.append(run_live_case(case, client, model))
        except Exception as exc:
            results.append({
                "case_id": case.get("id", "unknown"),
                "name": case.get("name", case.get("id", "unknown")),
                "mode": "live",
                "passed": False,
                "errors": [f"{type(exc).__name__}: {exc}"],
                "warnings": [],
                "checks": {},
            })
    return results


def write_results(results, mode):
    output = ROOT / "eval" / "results" / "eval_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "summary": {
            "total": len(results),
            "passed": sum(1 for item in results if item.get("passed")),
            "pass_rate": (
                sum(1 for item in results if item.get("passed")) / len(results)
                if results else 0.0
            ),
        },
        "cases": results,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output, payload


def main():
    parser = argparse.ArgumentParser(description="Evaluate biomodel-agent cases")
    parser.add_argument("--offline", action="store_true", help="run fixed IR regression cases")
    parser.add_argument("--live", action="store_true", help="run the real LLM agent")
    parser.add_argument("--case", default=None, help="run only one case id")
    parser.add_argument(
        "--cases-file",
        default=str(ROOT / "eval" / "cases" / "cases.json"),
        help="path to case JSON",
    )
    args = parser.parse_args()
    if args.offline and args.live:
        raise SystemExit("choose only one of --offline and --live")

    cases = load_cases(Path(args.cases_file))
    if args.live:
        results = run_live(cases, case_filter=args.case)
        mode = "live"
    else:
        selected = [c for c in cases if not args.case or c["id"] == args.case]
        with tempfile.TemporaryDirectory(prefix="biomodel_eval_") as tmp:
            results = []
            for case in selected:
                try:
                    results.append(run_offline_case(case, tmp))
                except Exception as exc:
                    results.append({
                        "case_id": case.get("id", "unknown"),
                        "name": case.get("name", case.get("id", "unknown")),
                        "mode": "offline",
                        "passed": False,
                        "errors": [f"{type(exc).__name__}: {exc}"],
                        "warnings": [],
                        "checks": {},
                    })
        mode = "offline"

    output, payload = write_results(results, mode)
    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(f"results: {output}")
    summary = payload["summary"]
    return 0 if summary["total"] > 0 and summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
