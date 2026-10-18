"""Unified command line interface for the literature and modeling layers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .contracts.extraction_to_model_ir import ExtractionConversionError, load_and_convert
from .literature.cli import main as literature_main
from .literature.io_utils import load_json, write_json
from .modeling.model_ir import validate_model_ir


for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


LITERATURE_COMMANDS = {
    "prepare",
    "prepare-doi",
    "prepare-dir",
    "convert",
    "validate",
    "render",
    "scaffold",
    "normalize",
    "self-review",
    "semantic-review",
    "lexicon",
    "export-parameters",
}


def _print_help() -> None:
    print("统一 Biomodeling 命令行\n")
    print("文献层：")
    print("  python -m biomodeling literature prepare <source> --out <source.json>")
    print("  python -m biomodeling literature validate <extraction.json> --final")
    print("  python -m biomodeling literature render <extraction.json> --out <crosswalk.md> --final")
    print("\n两项目桥梁：")
    print("  python -m biomodeling to-model-ir <extraction.json> --out <model_ir.json>")
    print("  python -m biomodeling to-model-ir <extraction.json> --out <model_ir.json> --strict")
    print("\n建模层：")
    print("  python -m biomodeling validate-model <model_ir.json> [--simulation]")
    print("  python -m biomodeling simulate <model_ir.json> --output-dir runs/demo")
    print("  python -m biomodeling demo")
    print("  python -m biomodeling agent --data <paper.pdf>")
    print("\n文献命令也可以省略 `literature` 前缀，例如 `prepare`。")


def _command_to_model_ir(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="biomodeling to-model-ir", description="把 A 格式 extraction 转换为 B 格式 Model IR")
    parser.add_argument("extraction", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=["reproduce", "self_derived"], default=None)
    parser.add_argument("--strict", action="store_true", help="只有可仿真的完整模型才成功")
    args = parser.parse_args(argv)
    try:
        model = load_and_convert(args.extraction, mode=args.mode, strict=args.strict)
    except ExtractionConversionError as exc:
        print(f"转换失败：{exc}", file=sys.stderr)
        return 2
    write_json(args.out, model)
    conversion = model.get("conversion", {})
    print(f"Model IR: {args.out}")
    print(f"model_ready: {conversion.get('model_ready', False)}")
    for warning in conversion.get("warnings") or []:
        print(f"WARNING: {warning}")
    return 0


def _command_validate_model(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="biomodeling validate-model")
    parser.add_argument("model", type=Path)
    parser.add_argument("--simulation", action="store_true", help="按可仿真标准校验")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_model_ir(load_json(args.model), for_simulation=args.simulation)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("VALID" if report["valid"] else "INVALID")
        for item in report["errors"]:
            print(f"ERROR: {item}")
        for item in report["warnings"]:
            print(f"WARNING: {item}")
    return 0 if report["valid"] else 1


def _command_simulate(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="biomodeling simulate")
    parser.add_argument("model", type=Path)
    parser.add_argument("--output-dir", default="runs/simulation")
    parser.add_argument("--tag", default="sim")
    args = parser.parse_args(argv)
    from .modeling.simulate import simulate_model

    result = simulate_model(load_json(args.model), output_dir=args.output_dir, tag=args.tag)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        _print_help()
        return 0
    command = args[0]
    rest = args[1:]
    if command in LITERATURE_COMMANDS:
        return literature_main(args)
    if command == "literature":
        return literature_main(rest)
    if command == "to-model-ir":
        return _command_to_model_ir(rest)
    if command == "validate-model":
        return _command_validate_model(rest)
    if command == "simulate":
        return _command_simulate(rest)
    if command == "demo":
        from .agent.main import run_demo

        return run_demo()
    if command == "agent":
        completed = subprocess.run(
            [sys.executable, "-m", "biomodeling.agent.main", *rest],
            check=False,
        )
        return completed.returncode
    _print_help()
    print(f"\n未知命令：{command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

