"""
tools.py — the tool functions exposed to the LLM agent, and their
OpenAI function-calling JSON declarations.

The tools cover the full assignment workflow:

  1. read_text             – read a literature text file.
  2. save_model_ir         – persist a Model IR (extracted or self-derived).
  3. simulate_model        – numerically solve an IR (ODE/PDE) and save
                            results + plot.
  4. save_report           – write a markdown report summarising the
                            reproduction / spontaneous-derivation workflow.
"""

import json
from datetime import datetime
from pathlib import Path

from ..modeling.model_ir import MODEL_DOC_SCHEMA, validate_model_ir
from ..modeling.simulate import simulate_model as _simulate_model
from ..report_validation import validate_report_content
from ..security_utils import (
    external_reads_allowed,
    is_within,
    require_project_path,
    safe_filename,
    safe_identifier,
)
from ..literature.extraction import read_and_chunk
from ..literature.io_utils import write_json, write_jsonl
from ..contracts.extraction_to_model_ir import load_and_convert

# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

def _coerce_model(model):
    """Normalise a `model` argument that the LLM may hand over as an object
    OR as a JSON-encoded string back into a dict. Some chat-completion models
    serialise complex nested tool arguments as a string; we accept both.
    """
    if isinstance(model, str):
        return json.loads(model)
    if isinstance(model, (list, tuple)) and model:
        # occasionally the model wraps the object in a list
        model = model[0]
    return model


# Result files under output/ (big numeric simulation JSON) are capped so the
# agent does not flood its context by re-reading them; literature text and PDFs
# are read in FULL so no pages are dropped.
RESULT_MAX_CHARS = 20000


def read_text(file_path: str):
    """Read a literature file and return its content as plain text.

    Supports:
      - .pdf  -> parsed via pdf_utils (PyMuPDF), layout-aware two-column handling
      - other extensions (.txt, .md, .tex, ...) -> read as UTF-8 text.

    Literature text is returned in full (never truncated), so every page of a
    paper reaches the agent. Only numeric result files under `output/` or
    `runs/` (e.g. simulation_*.json) are capped to avoid flooding the model context.
    """
    try:
        if external_reads_allowed():
            p = Path(file_path).expanduser().resolve()
        else:
            p = require_project_path(file_path)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not p.exists():
        return f"ERROR: file not found: {file_path}"

    is_result_file = any(part in {"output", "runs"} for part in p.parts) and p.suffix.lower() == ".json"

    if p.suffix.lower() == ".pdf":
        from ..modeling.pdf_utils import extract_pdf_text
        return extract_pdf_text(p)

    try:
        content = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = p.read_text(encoding="utf-8", errors="replace")

    # Only cap large numeric result files, never the literature itself.
    if is_result_file and len(content) > RESULT_MAX_CHARS:
        head = content[:RESULT_MAX_CHARS]
        return (
            f"[large result file {len(content)} chars; only first "
            f"{RESULT_MAX_CHARS} shown]\n\n" + head
        )
    return content



def save_model_ir(model, tag: str = None):
    """Persist a Model IR document to output/<slug>.json.

    `tag` lets one distinguish several IRs (e.g. the literature model vs a
    self-derived one).
    """
    model = _coerce_model(model)
    tag = safe_identifier(tag, default=None)
    validation = validate_model_ir(model)
    if not validation["valid"]:
        raise ValueError(
            "Invalid Model IR:\n"
            + "\n".join(f"- {item}" for item in validation["errors"])
        )

    output_dir = Path("runs") / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    from ..modeling.simulate import _model_slug
    slug = _model_slug(model)
    stem = f"model_ir_{slug}" if not tag else f"model_ir_{slug}__{tag}"
    path = output_dir / f"{stem}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

    return f"Model IR saved to {path}"


def simulate_model(model, tag: str = "sim"):
    """Numerically simulate a Model IR (ODE or PDE).

    Returns a JSON string describing the run, its output file paths and a
    short numeric summary. The parameters and initial conditions must have
    numeric values.
    """
    try:
        model = _coerce_model(model)
        result = _simulate_model(model, output_dir="runs/simulation", tag=tag)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:  # surface errors back to the agent
        return json.dumps(
            {
                "status": "error",
                "error": str(exc),
                "hint": (
                    "请检查 Model IR 是否给全了参数的 value 和 initial "
                    "conditions 的 value，并确认方程符号与 variables 一致。"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )


def save_report(title: str, content: str, filename: str = None, metadata: dict = None, strict: bool = False):
    """Save a markdown report to runs/reports/<name>.md.

    `content` should be full Markdown describing the modelling workflow,
    equations, simulation results and conclusions. Optional simulation
    metadata is embedded near the top of the report. In default mode, missing
    sections are warnings; strict mode rejects them.
    """
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object/dict")
    validation = validate_report_content(content, strict=strict)
    if not validation["valid"]:
        raise ValueError(
            "Report validation failed:\n"
            + "\n".join(f"- {item}" for item in validation["errors"])
        )
    out_dir = Path("runs") / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    name = filename or ("report_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    name = safe_filename(name)
    if not name.endswith(".md"):
        name += ".md"
    path = out_dir / name
    if not is_within(path, out_dir):
        raise ValueError("report path must stay inside runs/reports")

    header = f"# {title}\n\n"
    meta = (
        f"> generated by biomodel-agent on "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    )
    metadata_block = ""
    if metadata:
        metadata_block = (
            "## Run metadata\n\n```json\n"
            + json.dumps(metadata, ensure_ascii=False, indent=2)
            + "\n```\n\n"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + meta + metadata_block + content)

    message = f"Report saved to {path}"
    if validation["warnings"]:
        message += "\nvalidation warnings:\n- " + "\n- ".join(validation["warnings"])
    return message



def prepare_literature(source: str, out_dir: str = "runs/literature"):
    """Prepare a local paper or DOI with project A's evidence-aware pipeline."""
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = output_dir / "source.json"
    chunks_path = output_dir / "chunks.jsonl"
    local_path = Path(source)
    try:
        if local_path.is_file():
            prepared, chunks = read_and_chunk(local_path)
        else:
            from ..literature.doi import looks_like_doi, resolve_doi
            if not looks_like_doi(source):
                return json.dumps({"status": "error", "error": f"file or DOI not found: {source}"}, ensure_ascii=False)
            prepared, chunks, _document = resolve_doi(source)
        write_json(source_path, prepared)
        write_jsonl(chunks_path, chunks)
        return json.dumps({
            "status": "ok",
            "source": str(source_path),
            "chunks": str(chunks_path),
            "chunk_count": prepared.get("chunk_count"),
            "word_count": prepared.get("word_count"),
            "section_count": prepared.get("section_count"),
            "document": prepared.get("document"),
        }, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2)


def convert_extraction_to_model_ir(extraction_path: str, output_path: str = None, strict: bool = False):
    """Convert project A extraction JSON into project B Model IR JSON."""
    try:
        source = Path(extraction_path)
        target = Path(output_path) if output_path else Path("runs") / "model_ir_from_extraction.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        model = load_and_convert(source, strict=strict)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(model, handle, ensure_ascii=False, indent=2)
        conversion = model.get("conversion", {})
        return json.dumps({
            "status": "ok",
            "model_ir": str(target),
            "model_ready": conversion.get("model_ready", False),
            "warnings": conversion.get("warnings", []),
            "validation": conversion.get("validation_for_simulation", {}),
        }, ensure_ascii=False, indent=2)
    except Exception as exc:
        return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# OpenAI function-calling declarations
# ---------------------------------------------------------------------------

def _fn(name, description, parameters):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


TOOLS = [
    _fn(
        "read_text",
        "读取一个 UTF-8 文本文件（生物系统文献正文）并返回完整内容。",
        {
            "type": "object",
            "properties": {
                "file_path": {"type": "string",
                              "description": "需要读取的文本文件路径"},
            },
            "required": ["file_path"],
        },
    ),
    _fn(
        "save_model_ir",
        "把从论文中提取的，或自发构建的结构化数学模型保存为 Model IR JSON 文件。",
        {
            "type": "object",
            "properties": {
                "model": MODEL_DOC_SCHEMA,
                "tag": {
                    "type": "string",
                    "description": (
                        "可选标签，用于区分同一模型的不同 IR，如 "
                        "'reproduce'（复现文献）或 'self_derived'（自发构建）。"
                    ),
                },
            },
            "required": ["model"],
        },
    ),
    _fn(
        "simulate_model",
        "对给定 Model IR（ODE 或 PDE）做数值模拟求解，保存结果 JSON 和 PNG 图，"
        "返回运行的数值摘要（终值、峰值等）。要求参数和初值都有数值。",
        {
            "type": "object",
            "properties": {
                "model": MODEL_DOC_SCHEMA,
                "tag": {
                    "type": "string",
                    "description": "输出文件标签，如 'reproduce' 或 'self_derived'",
                },
            },
            "required": ["model"],
        },
    ),
    _fn(
        "prepare_literature",
        "用项目 A 的文献管线读取本地论文或 DOI，保存 source.json 与 chunks.jsonl，并返回分块统计。",
        {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "本地文献路径或 DOI"},
                "out_dir": {"type": "string", "description": "输出目录，默认 runs/literature"},
            },
            "required": ["source"],
        },
    ),
    _fn(
        "convert_extraction_to_model_ir",
        "把项目 A 格式的 extraction JSON 转为项目 B 的 Model IR，并报告该模型是否可直接仿真。",
        {
            "type": "object",
            "properties": {
                "extraction_path": {"type": "string", "description": "A 格式 extraction JSON 路径"},
                "output_path": {"type": "string", "description": "可选 Model IR 输出路径"},
                "strict": {"type": "boolean", "description": "仅允许可仿真的完整模型"},
            },
            "required": ["extraction_path"],
        },
    ),
    _fn(
        "save_report",
        "把本次建模/复现工作的完整过程和结论保存为 Markdown 报告到 "
        "runs/reports/ 目录。",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string",
                          "description": "报告标题"},
                "content": {"type": "string",
                            "description": "Markdown 格式的报告正文"},
                "filename": {"type": "string",
                             "description": "可选文件名（不含 .md 会自动补）"},
                "metadata": {
                    "type": "object",
                    "description": "可选运行元数据，通常使用 simulate_model 返回的 run_metadata",
                },
                "strict": {
                    "type": "boolean",
                    "description": "是否严格校验报告章节；默认 false，仅返回警告",
                },
            },
            "required": ["title", "content"],
        },
    ),
]

FUNCTIONS = {
    "read_text": read_text,
    "save_model_ir": save_model_ir,
    "simulate_model": simulate_model,
    "prepare_literature": prepare_literature,
    "convert_extraction_to_model_ir": convert_extraction_to_model_ir,
    "save_report": save_report,
}





