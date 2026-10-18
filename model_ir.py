"""
Model IR (Intermediate Representation) schema.

A Model IR is the structured, machine-readable description of a biological
mathematical model extracted from (or self-derived from) a paper. It is the
single contract between:

  * the LLM agent (which produces it from text),
  * the simulation engine (simulate.py) which turns it into a runnable
    ODE/PDE system and produces numeric results and plots.

The schema intentionally supports both ODE and PDE models.
"""


# ---------------------------------------------------------------------------
# Runtime validation
# ---------------------------------------------------------------------------

def _is_finite_number(value):
    """Return True only for finite real numbers (booleans are not numbers here)."""
    from math import isfinite
    from numbers import Real
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_model_ir(model, for_simulation=False):
    """Validate a Model IR beyond the JSON schema.

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
        }

    `for_simulation=True` additionally requires a complete, numerically
    runnable ODE/PDE model. Without it, incomplete scientific information is
    allowed for saved IR documents but structurally invalid fields are still
    rejected.
    """
    errors = []
    warnings = []

    if not isinstance(model, dict):
        return {
            "valid": False,
            "errors": ["model must be a JSON object"],
            "warnings": [],
        }

    required = [
        "model_name", "model_type", "description", "variables", "parameters",
        "equations", "domain", "initial_conditions", "boundary_conditions",
        "origin", "missing_information",
    ]
    for field in required:
        if field not in model:
            errors.append(f"missing required field: {field}")

    model_type = model.get("model_type")
    if model_type not in {"ODE", "PDE", "stochastic", "unknown"}:
        errors.append("model_type must be one of: ODE, PDE, stochastic, unknown")
    elif for_simulation and model_type not in {"ODE", "PDE"}:
        errors.append(
            f"Unsupported model_type '{model_type}'; only ODE and PDE are supported."
        )

    variables = model.get("variables")
    variable_names = []
    if not isinstance(variables, list) or not variables:
        errors.append("variables must be a non-empty list")
        variables = []
    else:
        for i, var in enumerate(variables):
            if not isinstance(var, dict):
                errors.append(f"variables[{i}] must be an object")
                continue
            name = var.get("name")
            if not _is_nonempty_string(name):
                errors.append(f"variables[{i}].name must be a non-empty string")
                continue
            if name in variable_names:
                errors.append(f"duplicate variable name: {name}")
            else:
                variable_names.append(name)
            if not _is_nonempty_string(var.get("description")):
                warnings.append(f"variables[{i}].description is missing or empty")
            if not _is_nonempty_string(var.get("unit")):
                warnings.append(f"variables[{i}].unit is missing or empty")

    parameters = model.get("parameters")
    parameter_names = []
    missing_parameters = []
    if not isinstance(parameters, list):
        errors.append("parameters must be a list")
        parameters = []
    for i, param in enumerate(parameters):
        if not isinstance(param, dict):
            errors.append(f"parameters[{i}] must be an object")
            continue
        name = param.get("name")
        if not _is_nonempty_string(name):
            errors.append(f"parameters[{i}].name must be a non-empty string")
            continue
        if name in parameter_names:
            errors.append(f"duplicate parameter name: {name}")
        else:
            parameter_names.append(name)
        value_known = param.get("value_known")
        if not isinstance(value_known, bool):
            errors.append(f"parameters[{i}].value_known must be boolean")
        elif value_known:
            if not _is_finite_number(param.get("value")):
                if for_simulation:
                    missing_parameters.append(name)
                else:
                    errors.append(
                        f"parameter '{name}' has value_known=true but no numeric value"
                    )
        elif param.get("value") is not None:
            warnings.append(f"parameter '{name}' has value but value_known=false; value is ignored")

    equations = model.get("equations")
    equation_vars = []
    if not isinstance(equations, list) or not equations:
        errors.append("equations must be a non-empty list")
        equations = []
    for i, eq in enumerate(equations):
        if not isinstance(eq, dict):
            errors.append(f"equations[{i}] must be an object")
            continue
        var = eq.get("variable")
        if not _is_nonempty_string(var):
            errors.append(f"equations[{i}].variable must be a non-empty string")
            continue
        if var not in variable_names:
            errors.append(f"equations[{i}] references unknown variable: {var}")
        if var in equation_vars:
            errors.append(f"duplicate equation for variable: {var}")
        else:
            equation_vars.append(var)
        if not _is_nonempty_string(eq.get("expression")):
            errors.append(f"equations[{i}].expression must be a non-empty string")

    missing_equations = [v for v in variable_names if v not in equation_vars]
    if missing_equations:
        errors.append(f"Equations missing for variables: {missing_equations}")

    domain = model.get("domain")
    t_start = None
    t_end = None
    if not isinstance(domain, dict):
        errors.append("domain must be an object")
        domain = {}
    else:
        t_start = domain.get("t_start")
        t_end = domain.get("t_end")
        if not _is_finite_number(t_start):
            errors.append("domain.t_start must be a finite number")
        if not _is_finite_number(t_end):
            errors.append("domain.t_end must be a finite number")
        if _is_finite_number(t_start) and _is_finite_number(t_end) and t_end <= t_start:
            errors.append("domain.t_end must be greater than domain.t_start")

        if model_type == "PDE":
            spatial = domain.get("spatial")
            if not isinstance(spatial, list) or not spatial:
                errors.append("PDE model requires a non-empty domain.spatial list")
            else:
                if len(spatial) != 1:
                    errors.append(
                        "PDE model currently supports exactly one spatial interval"
                    )
                for i, interval in enumerate(spatial):
                    if not isinstance(interval, dict):
                        errors.append(f"domain.spatial[{i}] must be an object")
                        continue
                    x_start = interval.get("x_start")
                    x_end = interval.get("x_end")
                    if not _is_finite_number(x_start):
                        errors.append(f"domain.spatial[{i}].x_start must be a finite number")
                    if not _is_finite_number(x_end):
                        errors.append(f"domain.spatial[{i}].x_end must be a finite number")
                    if _is_finite_number(x_start) and _is_finite_number(x_end) and x_end <= x_start:
                        errors.append(f"domain.spatial[{i}].x_end must be greater than x_start")
                    n_points = interval.get("n_points", 201)
                    if not isinstance(n_points, int) or isinstance(n_points, bool) or n_points < 3:
                        errors.append(f"domain.spatial[{i}].n_points must be an integer >= 3")

    initial_conditions = model.get("initial_conditions")
    ic_vars = []
    missing_ics = []
    if not isinstance(initial_conditions, list):
        errors.append("initial_conditions must be a list")
        initial_conditions = []
    for i, ic in enumerate(initial_conditions):
        if not isinstance(ic, dict):
            errors.append(f"initial_conditions[{i}] must be an object")
            continue
        var = ic.get("variable")
        if not _is_nonempty_string(var):
            errors.append(f"initial_conditions[{i}].variable must be a non-empty string")
            continue
        if var not in variable_names:
            errors.append(f"initial_conditions[{i}] references unknown variable: {var}")
        if var in ic_vars:
            errors.append(f"duplicate initial condition for variable: {var}")
        else:
            ic_vars.append(var)
        value_known = ic.get("value_known")
        if not isinstance(value_known, bool):
            errors.append(f"initial_conditions[{i}].value_known must be boolean")
            continue
        has_value = _is_finite_number(ic.get("value"))
        has_expr = _is_nonempty_string(ic.get("expr"))
        if value_known:
            if model_type == "ODE" and not has_value:
                errors.append(f"ODE initial condition for {var} requires a numeric value")
            elif not has_value and not has_expr:
                errors.append(f"initial condition for {var} requires value or expr")
        else:
            missing_ics.append(var)

    missing_ic_vars = [v for v in variable_names if v not in ic_vars]
    if missing_ic_vars:
        if for_simulation:
            missing_ics.extend(missing_ic_vars)
        else:
            warnings.append(f"initial_conditions does not cover variables: {missing_ic_vars}")
    if for_simulation and missing_ics:
        errors.append(f"Cannot simulate: missing initial conditions for {sorted(set(missing_ics))}.")

    boundary_conditions = model.get("boundary_conditions")
    bc_keys = []
    if not isinstance(boundary_conditions, list):
        errors.append("boundary_conditions must be a list")
        boundary_conditions = []
    for i, bc in enumerate(boundary_conditions):
        if not isinstance(bc, dict):
            errors.append(f"boundary_conditions[{i}] must be an object")
            continue
        var = bc.get("variable")
        boundary = bc.get("boundary")
        bc_type = bc.get("type")
        if var not in variable_names:
            errors.append(f"boundary_conditions[{i}] references unknown variable: {var}")
        if boundary not in {"left", "right"}:
            errors.append(f"boundary_conditions[{i}].boundary must be left or right")
        if bc_type not in {"dirichlet", "neumann"}:
            errors.append(f"boundary_conditions[{i}].type must be dirichlet or neumann")
        if not _is_finite_number(bc.get("value")):
            errors.append(f"boundary_conditions[{i}].value must be a finite number")
        key = (var, boundary)
        if key in bc_keys:
            errors.append(f"duplicate boundary condition for {var} {boundary}")
        else:
            bc_keys.append(key)

    origin = model.get("origin")
    if not isinstance(origin, dict):
        errors.append("origin must be an object")
    else:
        if origin.get("mode") not in {"reproduce", "self_derived"}:
            errors.append("origin.mode must be reproduce or self_derived")
        if not _is_nonempty_string(origin.get("source_text")):
            errors.append("origin.source_text must be a non-empty string")
        if origin.get("confidence") not in (None, "high", "medium", "low"):
            errors.append("origin.confidence must be high, medium, or low")
        elif origin.get("confidence") is None:
            warnings.append("origin.confidence is not set")
        if origin.get("assumptions") is not None and not isinstance(origin.get("assumptions"), list):
            errors.append("origin.assumptions must be a list")

    if model.get("missing_information") is not None and not isinstance(model.get("missing_information"), list):
        errors.append("missing_information must be a list")

    if for_simulation and missing_parameters:
        errors.append(
            f"Cannot simulate: parameters without numeric values: {missing_parameters}. "
            "请先在 IR 中提供参数数值。"
        )

    return {"valid": not errors, "errors": errors, "warnings": warnings}


# Base schema for functions that take a full model document.
MODEL_DOC_SCHEMA = {
    "type": "object",
    "properties": {
        "model_name": {
            "type": "string",
            "description": "模型的名称，如 'Lotka-Volterra predator-prey model'；未知填 unknown",
        },
        "model_type": {
            "type": "string",
            "enum": ["ODE", "PDE", "stochastic", "unknown"],
            "description": "模型类型：常微分方程 ODE、偏微分方程 PDE、随机模型 stochastic",
        },
        "description": {
            "type": "string",
            "description": (
                "一段简短的自然语言描述：说明了哪些生物实体（变量）参与、"
                "哪些相互作用/机制被纳入模型，以及模型描述了什么生物学过程。"
            ),
        },
        "variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string",
                                    "description": "该变量的生物学含义"},
                    "unit": {"type": "string",
                             "description": "单位，未知填 unknown"},
                },
                "required": ["name", "description", "unit"],
            },
        },
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string",
                                    "description": "参数的生物学含义（如出生率、扩散系数）"},
                    "value_known": {"type": "boolean",
                                    "description": "文献是否给出数值"},
                    "value": {"type": "number",
                              "description": "数值；value_known=false 时给 null 或缺失"},
                    "unit": {"type": "string"},
                },
                "required": ["name", "value_known", "unit"],
            },
        },
        "equations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "variable": {"type": "string",
                                 "description": "被求解的因变量名，如 X"},
                    "expression": {
                        "type": "string",
                        "description": (
                            "方程的右端项（对于 ODE 是 dV/dt = expr，对于 PDE 是 "
                            "dV/dt = expr，其中 expr 可用 x, t, 以及二阶导符号 "
                            "d2V/dx2 或 V_xx 表示空间扩散项）。"
                            "使用与 variables 中一致的符号。"
                        ),
                    },
                },
                "required": ["variable", "expression"],
            },
        },
        "domain": {
            "type": "object",
            "properties": {
                "t_start": {"type": "number",
                            "description": "时间起点，默认 0"},
                "t_end": {"type": "number",
                          "description": "时间终点"},
                "spatial": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "x_start": {"type": "number"},
                            "x_end": {"type": "number"},
                            "n_points": {"type": "integer",
                                         "description": "空间网格点数"},
                        },
                        "required": ["x_start", "x_end"],
                    },
                    "description": (
                        "PDE 的空间区间列表。当前求解器仅支持一维单区间；"
                        "未来将扩展为多区间和多维空间。"
                    ),
                },
            },
            "required": ["t_start", "t_end"],
        },
        "initial_conditions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "variable": {"type": "string"},
                    "value_known": {"type": "boolean"},
                    "value": {
                        "type": "number",
                        "description": "ODE 的常量初值；若为函数式初值（PDE），"
                                       "写在 initial_condition_expr 中",
                    },
                    "expr": {
                        "type": "string",
                        "description": "PDE 的函数式初值表达式，例如 'a*exp(-((x-mu)/s)**2)'，"
                                       "可用 x 和 parameters 中的参数名",
                    },
                },
                "required": ["variable", "value_known"],
            },
        },
        "boundary_conditions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "variable": {"type": "string"},
                    "boundary": {
                        "type": "string",
                        "enum": ["left", "right"],
                        "description": "空间边界：左端 x_start 或右端 x_end",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["dirichlet", "neumann"],
                        "description": "Dirichlet（值给定）或 Neumann（通量/梯度给定）",
                    },
                    "value": {"type": "number",
                              "description": "边界值"},
                },
                "required": ["variable", "boundary", "type", "value"],
            },
            "description": "PDE 的边界条件；ODE 模型可为空数组",
        },
        "origin": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["reproduce", "self_derived"],
                    "description": "reproduce=复现文献已有模型；self_derived=从文献自发构建",
                },
                "source_text": {
                    "type": "string",
                    "description": "模型来源：文献标题/引用，或 'self-derived'",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "对建模信心：高/中/低",
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "建模所依赖的生物学假设清单",
                },
            },
            "required": ["mode", "source_text"],
        },
        "missing_information": {
            "type": "array",
            "items": {"type": "string"},
            "description": "文献中缺失、但建模需要的所有信息清单",
        },
    },
    "required": [
        "model_name",
        "model_type",
        "description",
        "variables",
        "parameters",
        "equations",
        "domain",
        "initial_conditions",
        "boundary_conditions",
        "origin",
        "missing_information",
    ],
}

