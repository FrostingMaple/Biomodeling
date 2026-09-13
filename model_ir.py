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
                    "description": "PDE 的空间区间列表（一维 PDE 通常一个区间）",
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

