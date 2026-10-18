"""Markdown 建模报告的结构与完整性校验。"""

import re


def _contains_any(text, patterns):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def validate_report_content(content, strict=False):
    """Validate a modelling report.

    Default mode is intentionally soft: missing sections produce warnings so
    that reports generated from heterogeneous papers are not rejected merely
    because they use different headings. `strict=True` promotes warnings to
    errors.
    """
    errors = []
    warnings = []
    checks = {}

    if not isinstance(content, str) or not content.strip():
        return {
            "valid": False,
            "errors": ["report content must be a non-empty string"],
            "warnings": [],
            "checks": {},
        }

    text = content.strip()

    checks["equations"] = _contains_any(
        text,
        [r"方程", r"equation", r"\bode\b", r"\bpde\b", r"\bd[A-Za-z0-9_]+/dt\b"],
    )
    checks["parameters"] = _contains_any(
        text,
        [r"参数", r"parameter", r"parameter values", r"取值"],
    )
    checks["assumptions"] = _contains_any(
        text,
        [r"假设", r"assumption", r"hypothesis"],
    )
    checks["results"] = _contains_any(
        text,
        [r"模拟", r"结果", r"simulation", r"result", r"轨迹", r"稳态", r"峰值"],
    )
    checks["limitations"] = _contains_any(
        text,
        [r"局限", r"缺失", r"limitation", r"missing", r"不足"],
    )
    checks["conclusion"] = _contains_any(
        text,
        [r"结论", r"conclusion", r"总结"],
    )

    section_names = {
        "equations": "方程/模型定义",
        "parameters": "参数或参数来源",
        "assumptions": "建模假设",
        "results": "模拟/数值结果",
        "limitations": "缺失信息或局限性",
        "conclusion": "结论",
    }
    for key, label in section_names.items():
        if not checks[key]:
            warnings.append(f"missing section: {label}")

    if re.search(r"\b(?:TODO|TBD)\b|待补充|待完善", text, flags=re.IGNORECASE):
        warnings.append("report contains unfinished placeholders (TODO/TBD/待补充)")

    if strict:
        errors.extend(warnings)
        warnings = []

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
