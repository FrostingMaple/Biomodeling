"""
simulate.py — the numerical simulation engine for Model IR documents.

Given a Model IR (from model_ir.py), this engine:

  1. Validates the IR and resolves known parameter values.
  2. For ODE models: builds a right-hand side and integrates with scipy's
     solve_ivp (RK45 / LSODA).
  3. For PDE models (1-D reaction-diffusion type): discretises space with
     finite differences and integrates the resulting semi-discrete system
     with solve_ivp (method of lines). Spatial diffusion terms written as
     second derivatives (e.g. "D * d2U/dx2" or "D*U_xx") are handled with a
     standard centred difference stencil.
  4. Writes numeric results as JSON and renders plots to PNG.

Expressions are parsed with sympy so that equation text from the IR is
turned into safe, validated numeric functions rather than exec'd code.
"""

import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

try:
    # Keep matplotlib config/cache inside the workspace so it never tries to
    # write to the user's home directory.
    os.environ.setdefault(
        "MPLCONFIGDIR",
        str(Path(__file__).resolve().parent / "output" / ".mplconfig"),
    )
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")  # headless backend, no display needed
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception as exc:  # pragma: no cover - optional plotting
    HAVE_MPL = False
    print(f"[simulate] plotting disabled: {exc}")


# ---------------------------------------------------------------------------
# Symbol sanitisation
# ---------------------------------------------------------------------------

# Symbol names that collide with sympy's own singletons / reserved names and
# must never be used as the *real* sympy symbol in a parsed expression. When a
# user model uses one of these as a variable or parameter name, we transparently
# remap it to a safe placeholder token for evaluation.
import re as _re

# These are sympy singletons / well-known names that shadow user symbols.
_RESERVED = {
    "S", "I", "E", "N", "O", "Q", "B", "C", "K", "re", "im", "oo", "pi",
    "e", "gamma", "zoo", "nan", "true", "false", "None",
    "Integer", "Rational", "Float", "exp", "log", "sin", "cos",
    "tan", "Abs", "sqrt", "sign", "Heaviside", "DiracDelta", "Max", "Min",
}


def _safe_token(index):
    """Return a placeholder symbol token that cannot collide with user names."""
    return f"__bmo_var{index}__"


# ---------------------------------------------------------------------------
# ODE model
# ---------------------------------------------------------------------------

def _simulate_ode(model, resolved):
    """Integrate an ODE system described by `model`.

    Returns (t, dict_of_arrays).
    """
    import sympy as sp

    variables = [v["name"] for v in model["variables"]]
    param_names = [p["name"] for p in model["parameters"]]
    all_names = set(variables) | set(param_names)
    t0 = model["domain"].get("t_start", 0.0)
    t1 = model["domain"]["t_end"]

    eq_by_var = {eq["variable"]: eq["expression"] for eq in model["equations"]}
    missing = [v for v in variables if v not in eq_by_var]
    if missing:
        raise ValueError(f"Equations missing for variables: {missing}")

    # Build RHS sympy expressions per state variable, with sane symbol tokens.
    # Every variable -> its own token; reserved parameter names also -> tokens.
    var_token = {v: _safe_token(i) for i, v in enumerate(variables)}
    par_token = {}
    for i, pname in enumerate(param_names):
        if pname in _RESERVED or pname == "x" or pname in var_token:
            par_token[pname] = _safe_token(1000 + i)
    token_for = dict(var_token)
    token_for.update(par_token)

    def to_safe_token(expr_str):
        for name, tok in sorted(token_for.items(), key=lambda kv: -len(kv[0])):
            expr_str = _re.sub(rf"\b{_re.escape(name)}\b(?!_)", tok, expr_str)
        return expr_str

    rhs_sym = {}
    for var in variables:
        expr_str = _replace_tex_derivatives(eq_by_var[var], var)
        expr_str = to_safe_token(expr_str)
        sym = sp.sympify(expr_str)
        # parameters are concrete numbers -> substitute their tokens directly
        for pname, pval in resolved.items():
            tok = token_for.get(pname, pname)
            sym = sym.subs(sp.Symbol(tok), sp.Float(pval))
        rhs_sym[var] = sp.N(sym)

    # lambdify each rhs over the variable tokens
    rhs_funcs = {}
    free_syms = {}
    for var in variables:
        sym = rhs_sym[var]
        frees = sorted(str(s) for s in sym.free_symbols)
        free_syms[var] = frees
        if not frees:
            rhs_funcs[var] = lambda *a, _v=var, _s=sym: float(_s)
        else:
            func = sp.lambdify(frees, sym, modules=["numpy"])
            rhs_funcs[var] = func

    tok_to_var = {var_token[v]: v for v in variables}

    def rhs(t, y):
        state = {variables[i]: float(y[i]) for i in range(len(variables))}
        out = []
        for var in variables:
            frees = free_syms[var]
            args = [state[tok_to_var[f]] for f in frees]
            out.append(float(rhs_funcs[var](*args)))
        return out

    # Initial conditions.
    y0 = []
    ic_by_var = {ic["variable"]: ic for ic in model["initial_conditions"]}
    for var in variables:
        ic = ic_by_var.get(var)
        if ic is None or not ic.get("value_known", False):
            raise ValueError(
                f"No numeric initial condition for {var}; "
                f"simulation cannot proceed."
            )
        y0.append(float(ic["value"]))
    y0 = np.asarray(y0, dtype=float)

    t_eval = np.linspace(t0, t1, 2000)
    sol = solve_ivp(
        rhs, (t0, t1), y0, t_eval=t_eval,
        method="RK45", rtol=1e-7, atol=1e-9,
    )
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")

    result = {variables[i]: sol.y[i] for i in range(len(variables))}
    return sol.t, result, "ODE"


# ---------------------------------------------------------------------------
# PDE model (1-D reaction-diffusion, method of lines)
# ---------------------------------------------------------------------------

def _replace_tex_derivatives(expr_str, var):
    """Normalise common derivative notations for sympy.

    Converts things like d2U/dx2 or U_xx or dU/dx into sympy-friendly
    derivative expressions. For second (spatial) derivatives we substitute
    a flag token (D2__<var>) that the PDE discretiser replaces with a finite
    difference stencil. First-order spatial derivatives are also supported
    (D1__<var>).
    """
    import re

    # d2U/dx2  and  U_xx  ->  D2__U
    expr_str = re.sub(r"d2([A-Za-z_]\w*)/dx2", r"D2__\1", expr_str)
    expr_str = re.sub(r"([A-Za-z_]\w*)_xx\b", r"D2__\1", expr_str)
    # dU/dx  and  U_x  ->  D1__U
    expr_str = re.sub(r"d([A-Za-z_]\w*)/dx", r"D1__\1", expr_str)
    expr_str = re.sub(r"([A-Za-z_]\w*)_x\b", r"D1__\1", expr_str)
    return expr_str


def _simulate_pde(model, resolved):
    """Solve a 1-D reaction-diffusion PDE by the method of lines.

    Each state variable u_i(x, t) is discretised on a grid of n points.
    Spatial second derivatives are replaced by the centred stencil
    (u[k+1]-2u[k]+u[k-1])/dx^2 via the D2__V tokens introduced above.

    Returns (t, dict_of_arrays) where each array has shape (len(t), n).
    """
    import re
    import sympy as sp

    variables = [v["name"] for v in model["variables"]]
    param_names = [p["name"] for p in model["parameters"]]

    spatial = (model["domain"].get("spatial") or [])[0]
    x0 = spatial["x_start"]
    x1 = spatial["x_end"]
    n = int(spatial.get("n_points", 201))
    dx = (x1 - x0) / (n - 1)
    grid = np.linspace(x0, x1, n)

    # Build per-variable RHS given a full state vector (all variables on grid).
    eq_by_var = {eq["variable"]: eq["expression"] for eq in model["equations"]}
    missing = [v for v in variables if v not in eq_by_var]
    if missing:
        raise ValueError(f"Equations missing for variables: {missing}")

    # Symbol token map: every variable -> its own safe token; reserved
    # parameter names also -> tokens. 'x' and the D1__/D2__ markers are the
    # PDE primitives and are never remapped.
    var_token = {v: _safe_token(i) for i, v in enumerate(variables)}
    par_token = {}
    for i, pname in enumerate(param_names):
        if pname in _RESERVED or pname == "x" or pname in var_token:
            par_token[pname] = _safe_token(2000 + i)
    token_for = dict(var_token)
    token_for.update(par_token)

    def to_safe_token(expr_str):
        for name, tok in sorted(token_for.items(), key=lambda kv: -len(kv[0])):
            expr_str = _re.sub(rf"\b{_re.escape(name)}\b(?!_)", tok, expr_str)
        return expr_str

    # Each var -> (diffusion_coeff_token_func, reaction_func)
    parsed = {}
    for var in variables:
        expr_str = eq_by_var[var]
        expr_str = _replace_tex_derivatives(expr_str, var)
        tokens = _re.findall(r"D2__(\w+)", expr_str)
        expr_str = to_safe_token(expr_str)
        sym_expr = sp.sympify(expr_str)
        # Substitute known parameter values into the expression once, up front.
        for pname, pval in resolved.items():
            tok = token_for.get(pname, pname)
            sym_expr = sym_expr.subs(sp.Symbol(tok), sp.Float(pval))
        parsed[var] = {
            "diff2": tokens,          # original user variable names under d2/dx2
            "sym_expr": sym_expr,
        }

    # Boundary conditions lookup.
    bc_by = {}
    for bc in model.get("boundary_conditions", []):
        key = (bc["variable"], bc["boundary"])
        bc_by[key] = bc

    var_to_idx = {var: i for i, var in enumerate(variables)}
    tok_to_var = {var_token[v]: v for v in variables}

    def state_to_arrays(y):
        return {var_token[v]: y[i * n:(i + 1) * n]
                for i, v in enumerate(variables)}

    def rhs(t, y):
        states = state_to_arrays(y)
        dy = np.zeros_like(y)
        for var in variables:
            info = parsed[var]
            idx = var_to_idx[var]
            u = states[var_token[var]]
            dudt = np.zeros(n)
            # Diffusion term via centred stencil, coefficient = multiplier of
            # each D2__diff_var token in the expression.
            for diff_var in info["diff2"]:
                coeff = sp.diff(info["sym_expr"], sp.Symbol(f"D2__{diff_var}"))
                coeff = sp.N(coeff)
                coeff_func = sp.lambdify("x", coeff, modules=["numpy"])
                c = np.asarray(coeff_func(grid), dtype=float)
                lap = np.zeros(n)
                lap[1:-1] = (u[:-2] - 2 * u[1:-1] + u[2:]) / dx**2
                dudt += c * lap
            # Reaction part: drop derivative tokens and evaluate pointwise.
            react_expr = info["sym_expr"].subs(
                {sp.Symbol(f"D2__{dv}"): 0 for dv in info["diff2"]}
            )
            react_expr = sp.N(react_expr)
            frees = sorted(str(s) for s in react_expr.free_symbols)
            if not frees:
                react_vals = np.full(n, float(react_expr))
            else:
                react_func = sp.lambdify(frees, react_expr, modules=["numpy"])
                args = [
                    grid if sf == "x" else states[sf]
                    for sf in frees
                ]
                react_vals = react_func(*args)
            dudt = dudt + np.asarray(react_vals, dtype=float)
            # Boundary conditions.
            for bnd, interior in (("left", 0), ("right", -1)):
                bc = bc_by.get((var, bnd))
                if bc is not None:
                    if bc["type"] == "dirichlet":
                        dudt[interior] = 0.0  # held fixed
                    else:  # neumann: zero-flux approximation does nothing here
                        pass
            dy[idx * n:(idx + 1) * n] = dudt
        return dy

    # Initial conditions (functional or constant) and boundary conditions.
    y0 = np.zeros(len(variables) * n)
    ic_by_var = {ic["variable"]: ic for ic in model["initial_conditions"]}
    for var in variables:
        idx = var_to_idx[var]
        ic = ic_by_var.get(var)
        if ic is None or not ic.get("value_known", False):
            raise ValueError(f"No initial condition for {var}.")
        if ic.get("expr"):
            ic_str = to_safe_token(ic["expr"])
            ic_expr = sp.sympify(ic_str)
            for pname, pval in resolved.items():
                tok = token_for.get(pname, pname)
                ic_expr = ic_expr.subs(sp.Symbol(tok), sp.Float(pval))
            func = sp.lambdify("x", sp.N(ic_expr), modules=["numpy"])
            y0[idx * n:(idx + 1) * n] = np.asarray(func(grid), dtype=float)
        else:
            y0[idx * n:(idx + 1) * n] = float(ic["value"])

    sol = solve_ivp(
        rhs, (model["domain"]["t_start"], model["domain"]["t_end"]),
        y0, t_eval=np.linspace(model["domain"]["t_start"],
                               model["domain"]["t_end"], 200),
        method="BDF", rtol=1e-5, atol=1e-6,
    )
    if not sol.success:
        raise RuntimeError(f"PDE solve_ivp failed: {sol.message}")

    result = {}
    for var in variables:
        idx = var_to_idx[var]
        result[var] = sol.y[idx * n:(idx + 1) * n].T  # (len(t), n)
    return sol.t, result, "PDE", grid


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def _resolve_parameters(model):
    """Return dict of parameter name -> numeric value for known ones."""
    resolved = {}
    unresolved = []
    for p in model["parameters"]:
        if p.get("value_known", False) and p.get("value") is not None:
            resolved[p["name"]] = float(p["value"])
        else:
            unresolved.append(p["name"])
    return resolved, unresolved


def _model_slug(model):
    """Safe filesystem identifier derived from the model name."""
    import re
    name = model.get("model_name") or "model"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return slug or "model"


def simulate_model(model: dict, output_dir: str = "output", tag: str = None):
    """Run the simulation for a Model IR.

    Returns a dict with metadata and file paths (JSON + PNG), or raises on
    invalid / non-simulatable input. `tag` optionally distinguishes runs of
    the same model (e.g. "reproduce" vs "self_derived_goal").
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = _model_slug(model)
    stem = f"{slug}" if not tag else f"{slug}__{tag}"

    model_type = model.get("model_type", "unknown")
    resolved, unresolved = _resolve_parameters(model)
    if unresolved:
        raise ValueError(
            f"Cannot simulate: parameters without numeric values: {unresolved}. "
            f"请先在 IR 中提供参数数值。"
        )

    missing_ic = [
        ic["variable"] for ic in model["initial_conditions"]
        if not ic.get("value_known", False)
    ]
    if missing_ic:
        raise ValueError(
            f"Cannot simulate: missing initial conditions for {missing_ic}."
        )

    if model_type == "ODE":
        t, result, kind = _simulate_ode(model, resolved)
        grid = None
    elif model_type == "PDE":
        t, result, kind, grid = _simulate_pde(model, resolved)
    else:
        raise ValueError(
            f"Unsupported model_type '{model_type}'; only ODE and PDE are supported."
        )

    # Save numeric results.
    results_path = output_dir / f"simulation_{stem}.json"
    serialized = {
        "model_name": model.get("model_name"),
        "model_type": model_type,
        "t": list(map(float, t)),
    }
    for var, arr in result.items():
        if model_type == "PDE":
            serialized[var] = arr.tolist()
        else:
            serialized[var] = list(map(float, arr))
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2, ensure_ascii=False)

    # Render plot.
    plot_path = output_dir / f"simulation_{stem}.png"
    if HAVE_MPL:
        _render_plot(model, model_type, t, result, grid, plot_path)
    else:
        plot_path = None

    summary = _summarize(model, model_type, t, result, grid)

    return {
        "status": "ok",
        "model_name": model.get("model_name"),
        "model_type": model_type,
        "t_range": [float(t[0]), float(t[-1])],
        "results_file": str(results_path),
        "plot_file": str(plot_path) if plot_path else None,
        "summary": summary,
    }


def _render_plot(model, model_type, t, result, grid, plot_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    if model_type == "ODE":
        ax1, ax2 = axes
        for var, arr in result.items():
            ax1.plot(t, arr, label=var)
        ax1.set_xlabel("t")
        ax1.set_ylabel("population / value")
        ax1.set_title(model.get("model_name", "ODE model"))
        ax1.legend()
        ax1.grid(alpha=0.3)
        # Phase-space: first two variables.
        vnames = list(result.keys())
        if len(vnames) >= 2:
            ax2.plot(result[vnames[0]], result[vnames[1]])
            ax2.set_xlabel(vnames[0])
            ax2.set_ylabel(vnames[1])
            ax2.set_title("phase space")
            ax2.grid(alpha=0.3)
        else:
            ax2.axis("off")
    else:
        # PDE: show the last time snapshot per variable.
        for var, arr in result.items():
            axes[0].plot(grid, arr[-1], label=var)
        axes[0].set_xlabel("x")
        axes[0].set_ylabel("value")
        axes[0].set_title(f"{model.get('model_name','PDE')} @ t={t[-1]:.2f}")
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        # heatmap of the first variable over time-space
        first = list(result.keys())[0]
        im = axes[1].imshow(
            result[first].T, aspect="auto", origin="lower",
            extent=[t[0], t[-1], grid[0], grid[-1]])
        axes[1].set_xlabel("t")
        axes[1].set_ylabel("x")
        axes[1].set_title(f"{first}(x, t) heatmap")
        fig.colorbar(im, ax=axes[1])
    fig.tight_layout()
    fig.savefig(plot_path, dpi=130)
    plt.close(fig)


def _summarize(model, model_type, t, result, grid):
    """Produce a compact, quantitative summary of a completed simulation.

    The returned dict is what the LLM agent sees from the simulate tool, so it
    should contain enough numbers (peaks, troughs, final/steady states, period
    estimate, wavefront speed) that the agent does NOT need to open the large
    results JSON.
    """
    if model_type == "ODE":
        summary = {"type": "ODE"}
        peaks, troughs, periods = {}, {}, {}
        for var, arr in result.items():
            final = float(arr[-1])
            imax = int(np.argmax(arr))
            imin = int(np.argmin(arr))
            peak_v, peak_t = float(arr[imax]), float(t[imax])
            trough_v, trough_t = float(arr[imin]), float(t[imin])
            # estimate period from successive local maxima if oscillating
            period = None
            if len(arr) > 40:
                d = np.diff(np.sign(np.diff(arr)))
                maxima = np.where(d < 0)[0]
                if len(maxima) >= 2:
                    dts = np.diff(t[maxima])
                    median_dt = float(np.median(dts))
                    if median_dt > 1e-9 and np.ptp(dts) / median_dt < 0.3:
                        period = median_dt
            peaks[var] = {"peak_value": peak_v, "t_at_peak": peak_t}
            troughs[var] = {"trough_value": trough_v, "t_at_trough": trough_t}
            periods[var] = period
        summary["final_state"] = {v: float(result[v][-1]) for v in result}
        summary["maxima"] = peaks
        summary["minima"] = troughs
        summary["period_estimate"] = periods
        summary["hint"] = (
            "模拟的量化数值（终值、峰值、谷值、周期）已在此摘要中给出，"
            "无需再读取 results JSON 文件。"
        )
        return summary
    else:
        # PDE: report final spatial profile stats and, if a traveling wave is
        # present, estimate its propagation speed.
        summary = {"type": "PDE"}
        final = {}
        speeds = {}
        for var, arr in result.items():
            last_profile = np.asarray(arr[-1])
            final[var] = {
                "min": float(last_profile.min()),
                "max": float(last_profile.max()),
                "value_at_midpoint": float(last_profile[len(last_profile) // 2]),
                "spread": float(np.sum(last_profile > 0.5)),  # width of u>0.5 region (in grid points)
            }
            # wavefront speed: track x where u crosses 0.5 (first crossing from
            # left) over time.
            n_t, n_x = arr.shape
            spacer = np.linspace(
                model["domain"]["spatial"][0]["x_start"],
                model["domain"]["spatial"][0]["x_end"], n_x)
            crossings = []
            for i in range(0, n_t, max(1, n_t // 50)):
                row = arr[i]
                idx = np.where(row >= 0.5)[0]
                if len(idx):
                    crossings.append((t[i], float(spacer[idx[0]])))
            if len(crossings) >= 2:
                xs = np.array([c[1] for c in crossings])
                ts = np.array([c[0] for c in crossings])
                # use a robust slope over the linear region
                if len(xs) > 4:
                    p = np.polyfit(ts, xs, 1)
                    speeds[var] = float(p[0])
                else:
                    speeds[var] = None
            else:
                speeds[var] = None
            summary["final_profile"] = final
            summary["wavefront_speed_estimate"] = speeds

        D_vars = [p["name"] for p in model["parameters"] if p["name"].lower() == "d"]
        r_vars = [p["name"] for p in model["parameters"] if p["name"].lower() in ("r", "k")]
        if D_vars and r_vars:
            # c = 2*sqrt(D*r) for FKPP-type; report for comparison
            vals = {p["name"]: p.get("value") for p in model["parameters"]}
            try:
                summary["theoretical_fkpp_speed_2sqrt(Dr)"] = \
                    2.0 * (vals[D_vars[0]] * vals[r_vars[0]]) ** 0.5
            except Exception:
                pass
        summary["hint"] = (
            "波速估计与终态空间分布已给出；无需再读取 results JSON 文件。"
        )
        return summary


__all__ = ["simulate_model"]
