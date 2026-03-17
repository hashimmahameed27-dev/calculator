from flask import Flask, request, render_template_string
import math
import io
import base64

import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# Simple in-memory history for this server process
history = []
MAX_HISTORY = 20


def safe_eval(expr: str, x_value: float | None = None) -> float:
    """Evaluate a math expression safely with support for trig/exponential functions."""
    allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
    allowed_names["pi"] = math.pi
    allowed_names["e"] = math.e
    if x_value is not None:
        allowed_names["x"] = x_value

    return eval(expr, {"__builtins__": {}}, allowed_names)


HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Calculator • Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      :root {
        --bg: #0b1020;
        --bg-card: #0f172a;
        --border-subtle: rgba(148, 163, 184, 0.3);
        --accent: #22c55e;
        --accent-soft: rgba(34, 197, 94, 0.16);
        --accent-strong: #16a34a;
        --text: #f9fafb;
        --text-muted: #9ca3af;
        --danger: #fb7185;
      }

      *,
      *::before,
      *::after {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: radial-gradient(circle at top, #111827, #020617);
        color: var(--text);
      }

      .shell {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
      }

      .layout {
        width: 100%;
        max-width: 800px;
        display: grid;
        grid-template-columns: minmax(0, 220px) minmax(0, 1fr);
        gap: 1.25rem;
      }

      .card {
        position: relative;
        border-radius: 1rem;
        padding: 1.75rem 1.5rem 1.5rem;
        background: radial-gradient(circle at top left, rgba(34, 197, 94, 0.22), transparent 55%),
                    radial-gradient(circle at bottom right, rgba(45, 212, 191, 0.22), transparent 55%),
                    var(--bg-card);
        border: 1px solid var(--border-subtle);
        box-shadow:
          0 22px 45px rgba(15, 23, 42, 0.75),
          0 0 0 1px rgba(15, 23, 42, 0.9);
        overflow: hidden;
      }

      .history {
        border-radius: 1rem;
        padding: 1rem;
        background: radial-gradient(circle at top right, rgba(45, 212, 191, 0.18), transparent 60%),
                    rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(148, 163, 184, 0.35);
        box-shadow:
          0 18px 35px rgba(15, 23, 42, 0.8),
          0 0 0 1px rgba(15, 23, 42, 0.85);
        display: flex;
        flex-direction: column;
        min-height: 260px;
        max-height: 420px;
      }

      .history-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.6rem;
      }

      .history-title {
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #e5e7eb;
      }

      .history-count {
        font-size: 0.7rem;
        color: #9ca3af;
      }

      .history-list {
        margin: 0;
        padding: 0;
        list-style: none;
        font-size: 0.8rem;
        color: #d1d5db;
        overflow-y: auto;
        margin-top: 0.4rem;
      }

      .history-empty {
        margin-top: 0.75rem;
        font-size: 0.8rem;
        color: #9ca3af;
      }

      .history-item {
        padding: 0.35rem 0.1rem;
        border-bottom: 1px solid rgba(31, 41, 55, 0.9);
        display: flex;
        flex-direction: column;
        gap: 0.18rem;
      }

      .history-item:last-child {
        border-bottom: none;
      }

      .history-expression {
        color: #9ca3af;
      }

      .history-result {
        font-weight: 600;
        color: #e5e7eb;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 1.25rem;
      }

      .title {
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: 0.03em;
      }

      .badge {
        font-size: 0.75rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid rgba(34, 197, 94, 0.5);
        color: #86efac;
      }

      .credit {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
        letter-spacing: 0.02em;
      }

      .subtitle {
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-bottom: 1.25rem;
      }

      .display {
        border-radius: 0.9rem;
        padding: 0.6rem 0.75rem;
        margin-bottom: 0.9rem;
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(34, 197, 94, 0.65);
        text-align: right;
      }

      .display-main {
        font-size: 1.6rem;
        font-variant-numeric: tabular-nums;
      }

      .display-sub {
        margin-top: 0.1rem;
        font-size: 0.8rem;
        color: var(--text-muted);
      }

      form {
        display: grid;
        gap: 0.85rem;
      }

      label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9ca3af;
        margin-bottom: 0.2rem;
        display: block;
      }

      .row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
      }

      input,
      select {
        width: 100%;
        border-radius: 0.65rem;
        border: 1px solid rgba(148, 163, 184, 0.35);
        padding: 0.55rem 0.7rem;
        background: rgba(15, 23, 42, 0.85);
        color: var(--text);
        font-size: 0.9rem;
        outline: none;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
      }

      input::placeholder {
        color: rgba(148, 163, 184, 0.7);
      }

      input:focus,
      select:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.4);
        background: rgba(15, 23, 42, 0.95);
      }

      select {
        cursor: pointer;
      }

      button {
        margin-top: 0.25rem;
        width: 100%;
        border-radius: 999px;
        border: none;
        padding: 0.7rem 0.75rem;
        font-size: 0.88rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        cursor: pointer;
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: white;
        box-shadow:
          0 10px 22px rgba(22, 163, 74, 0.6),
          0 0 0 1px rgba(34, 197, 94, 0.9);
        transition: transform 0.08s ease, box-shadow 0.08s ease, filter 0.08s ease;
      }

      button:hover {
        filter: brightness(1.06);
        box-shadow:
          0 14px 28px rgba(22, 163, 74, 0.7),
          0 0 0 1px rgba(34, 197, 94, 1);
      }

      button:active {
        transform: translateY(1px);
        box-shadow:
          0 9px 18px rgba(22, 163, 74, 0.55),
          0 0 0 1px rgba(34, 197, 94, 0.9);
      }

      .result,
      .error {
        margin-top: 1rem;
        border-radius: 0.75rem;
        padding: 0.7rem 0.8rem;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        border: 1px solid rgba(148, 163, 184, 0.45);
        background: rgba(15, 23, 42, 0.9);
      }

      .result::before {
        content: "✓";
        font-size: 0.9rem;
        color: #bbf7d0;
      }

      .error {
        border-color: rgba(248, 113, 113, 0.8);
        background: rgba(127, 29, 29, 0.45);
        color: #fee2e2;
      }

      .error::before {
        content: "!";
        font-weight: 700;
        font-size: 0.9rem;
      }

      .expression {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-top: 0.2rem;
      }

      .site-footer {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
        font-size: 0.75rem;
        color: var(--text-muted);
        text-align: center;
      }

      @media (max-width: 768px) {
        .layout {
          grid-template-columns: minmax(0, 1fr);
        }

        .history {
          order: 2;
          max-height: 260px;
        }

        .card {
          order: 1;
          padding: 1.4rem 1.1rem 1.1rem;
        }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="layout">
        <aside class="history">
          <div class="history-header">
            <div class="history-title">History</div>
            <div class="history-count">
              {% if history %}
                {{ history|length }} item{% if history|length != 1 %}s{% endif %}
              {% else %}
                Empty
              {% endif %}
            </div>
          </div>

          {% if history %}
            <ul class="history-list">
              {% for item in history %}
                <li class="history-item">
                  <span class="history-expression">{{ item.expression }}</span>
                  <span class="history-result">{{ item.result }}</span>
                </li>
              {% endfor %}
            </ul>
          {% else %}
            <div class="history-empty">
              No calculations yet. Results you compute will appear here.
            </div>
          {% endif %}
        </aside>

        <div class="card">
          <div class="card-header">
            <div class="title">Calculator</div>
            <div class="badge">Python • Flask</div>
          </div>
          <div class="credit">Built & designed by Hashim Mahameed</div>
          <div class="subtitle">
            Enter two values, pick an operation, and get the result instantly.
          </div>

          <div class="display">
            <div class="display-main">
              {% if result is not none %}
                {{ result }}
              {% elif num1 or num2 %}
                {{ num1 or "0" }} {{ op or "+" }} {{ num2 or "0" }}
              {% else %}
                0
              {% endif %}
            </div>
            <div class="display-sub">
              {% if expression %}
                {{ expression }}
              {% else %}
                Ready
              {% endif %}
            </div>
          </div>

          <form method="post" novalidate>
            <div class="row">
              <div>
                <label for="num1">First value</label>
              <input
                  id="num1"
                  type="text"
                  name="num1"
                  inputmode="decimal"
                  value="{{ num1 or '' }}"
                  required
                >
              </div>
              <div>
                <label for="num2">Second value</label>
              <input
                  id="num2"
                  type="text"
                  name="num2"
                  inputmode="decimal"
                  value="{{ num2 or '' }}"
                  required
                >
              </div>
            </div>

            <div>
              <label for="op">Operation</label>
              <select id="op" name="op">
                <option value="+" {% if op == '+' %}selected{% endif %}>Add (+)</option>
                <option value="-" {% if op == '-' %}selected{% endif %}>Subtract (-)</option>
                <option value="*" {% if op == '*' %}selected{% endif %}>Multiply (×)</option>
                <option value="/" {% if op == '/' %}selected{% endif %}>Divide (÷)</option>
              </select>
            </div>

            <button type="submit">Compute</button>
          </form>

          {% if error %}
            <div class="error">{{ error }}</div>
          {% elif result is not none %}
            <div class="result">
              {{ result }}
            </div>
            {% if expression %}
              <div class="expression">{{ expression }}</div>
            {% endif %}
          {% endif %}

          <hr style="margin: 1.4rem 0; border: none; border-top: 1px solid rgba(30,64,175,0.6);" />

          <div class="subtitle">
            Advanced mode: use functions like <code>sin(x)</code>, <code>cos(x)</code>, <code>exp(x)</code>, <code>log(x)</code>, and constants <code>pi</code>, <code>e</code>.
          </div>

          <form method="post" novalidate>
            <input type="hidden" name="mode" value="advanced">
            <div>
              <label for="expression">Expression</label>
              <input
                id="expression"
                type="text"
                name="expression"
                inputmode="text"
                value="{{ adv_expression or '' }}"
                required
              >
            </div>

            <div class="row">
              <div>
                <label for="x_from">Graph from x =</label>
                <input
                  id="x_from"
                  type="text"
                  name="x_from"
                  inputmode="decimal"
                  value="{{ x_from or '-10' }}"
                >
              </div>
              <div>
                <label for="x_to">to x =</label>
                <input
                  id="x_to"
                  type="text"
                  name="x_to"
                  inputmode="decimal"
                  value="{{ x_to or '10' }}"
                >
              </div>
            </div>

            <div style="display:flex; align-items:center; gap:0.4rem; margin-top:0.3rem;">
              <input id="graph" type="checkbox" name="graph" {% if graph_requested %}checked{% endif %}>
              <label for="graph" style="margin:0; text-transform:none; letter-spacing:0; font-size:0.8rem;">
                Plot this expression as a graph
              </label>
            </div>

            <button type="submit">Evaluate / Graph</button>
          </form>

          {% if adv_error %}
            <div class="error">{{ adv_error }}</div>
          {% elif adv_result is not none %}
            <div class="result">
              {{ adv_result }}
            </div>
            {% if adv_expression %}
              <div class="expression">{{ adv_expression }}</div>
            {% endif %}
          {% endif %}

          {% if graph_url %}
            <div style="margin-top: 1rem; border-radius: 0.75rem; overflow: hidden; border: 1px solid rgba(30,64,175,0.8); background: #020617;">
              <img src="{{ graph_url }}" alt="Function graph" style="display:block; width:100%; height:auto;">
            </div>
          {% endif %}

          <hr style="margin: 1.4rem 0; border: none; border-top: 1px solid rgba(30,64,175,0.6);" />

          <div class="subtitle">
            Simultaneous equations (2×2): solve for <code>x</code> and <code>y</code> in:
            <code>a·x + b·y = c</code> and <code>d·x + e·y = f</code>
          </div>

          <form method="post" novalidate>
            <input type="hidden" name="mode" value="simul">

            <div class="row">
              <div>
                <label for="a">a</label>
                <input id="a" type="text" name="a" inputmode="decimal" value="{{ s_a or '' }}" required>
              </div>
              <div>
                <label for="b">b</label>
                <input id="b" type="text" name="b" inputmode="decimal" value="{{ s_b or '' }}" required>
              </div>
            </div>
            <div>
              <label for="c">c</label>
              <input id="c" type="text" name="c" inputmode="decimal" value="{{ s_c or '' }}" required>
            </div>

            <div class="row">
              <div>
                <label for="d">d</label>
                <input id="d" type="text" name="d" inputmode="decimal" value="{{ s_d or '' }}" required>
              </div>
              <div>
                <label for="e">e</label>
                <input id="e" type="text" name="e" inputmode="decimal" value="{{ s_e or '' }}" required>
              </div>
            </div>
            <div>
              <label for="f">f</label>
              <input id="f" type="text" name="f" inputmode="decimal" value="{{ s_f or '' }}" required>
            </div>

            <button type="submit">Solve (x, y)</button>
          </form>

          {% if simul_error %}
            <div class="error">{{ simul_error }}</div>
          {% elif simul_result is not none %}
            <div class="result">
              x = {{ simul_result.x }}, y = {{ simul_result.y }}
            </div>
            <div class="expression">
              {{ simul_expression }}
            </div>
          {% endif %}

          <footer class="site-footer">
            © 2025 Hashim Mahameed. All rights reserved.
          </footer>
        </div>
      </div>
    </div>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def calculator():
    global history

    num1 = num2 = op = ""
    result = None
    error = None
    expression = ""
    adv_expression = ""
    adv_result = None
    adv_error = None
    graph_url = None
    x_from = ""
    x_to = ""
    graph_requested = False
    simul_error = None
    simul_expression = ""
    simul_result = None
    s_a = s_b = s_c = s_d = s_e = s_f = ""

    if request.method == "POST":
        mode = request.form.get("mode", "basic")

        if mode == "advanced":
            adv_expression = request.form.get("expression", "").strip()
            x_from = request.form.get("x_from", "-10").strip()
            x_to = request.form.get("x_to", "10").strip()
            graph_requested = request.form.get("graph") is not None

            try:
                # Evaluate expression as a scalar. If it depends on x, skip scalar
                # evaluation and only use it for graphing.
                try:
                    adv_result = safe_eval(adv_expression)
                except NameError:
                    adv_result = None

                if graph_requested:
                    start = float(x_from or "-10")
                    end = float(x_to or "10")
                    if start >= end:
                        raise ValueError("Start of range must be less than end.")

                    xs = np.linspace(start, end, 400)
                    ys = []
                    for x_val in xs:
                        try:
                            ys.append(safe_eval(adv_expression, x_val))
                        except Exception:
                            ys.append(float("nan"))

                    fig, ax = plt.subplots(figsize=(4, 2.5), dpi=150)
                    ax.plot(xs, ys, color="#4f46e5", linewidth=1.5)
                    ax.set_facecolor("#020617")
                    fig.patch.set_facecolor("#020617")
                    ax.grid(True, color="#1f2937", linewidth=0.5)
                    ax.spines["bottom"].set_color("#9ca3af")
                    ax.spines["left"].set_color("#9ca3af")
                    ax.tick_params(colors="#9ca3af", labelsize=7)

                    buf = io.BytesIO()
                    plt.tight_layout()
                    fig.savefig(buf, format="png", bbox_inches="tight")
                    plt.close(fig)
                    buf.seek(0)
                    graph_url = "data:image/png;base64," + base64.b64encode(buf.read()).decode(
                        "ascii"
                    )

                # Add to history
                history.insert(
                    0,
                    {
                        "expression": adv_expression,
                        "result": adv_result,
                    },
                )
                history[:] = history[:MAX_HISTORY]
            except Exception as exc:  # noqa: BLE001
                adv_error = f"Could not evaluate expression: {exc}"
        elif mode == "simul":
            s_a = request.form.get("a", "").strip()
            s_b = request.form.get("b", "").strip()
            s_c = request.form.get("c", "").strip()
            s_d = request.form.get("d", "").strip()
            s_e = request.form.get("e", "").strip()
            s_f = request.form.get("f", "").strip()

            try:
                a = float(s_a)
                b = float(s_b)
                c = float(s_c)
                d = float(s_d)
                e = float(s_e)
                f = float(s_f)

                A = np.array([[a, b], [d, e]], dtype=float)
                B = np.array([c, f], dtype=float)

                det = float(np.linalg.det(A))
                if abs(det) < 1e-12:
                    raise ValueError("No unique solution (determinant is 0).")

                sol = np.linalg.solve(A, B)
                x_val = float(sol[0])
                y_val = float(sol[1])

                simul_result = {"x": x_val, "y": y_val}
                simul_expression = f"{a}·x + {b}·y = {c}  and  {d}·x + {e}·y = {f}"

                history.insert(
                    0,
                    {
                        "expression": simul_expression,
                        "result": f"x={x_val}, y={y_val}",
                    },
                )
                history[:] = history[:MAX_HISTORY]
            except Exception as exc:  # noqa: BLE001
                simul_error = f"Could not solve: {exc}"
        else:
            num1 = request.form.get("num1", "").strip()
            num2 = request.form.get("num2", "").strip()
            op = request.form.get("op", "+")

            try:
                a = float(num1)
                b = float(num2)

                if op == "+":
                    result = a + b
                elif op == "-":
                    result = a - b
                elif op == "*":
                    result = a * b
                elif op == "/":
                    if b == 0:
                        error = "Error: Cannot divide by zero."
                    else:
                        result = a / b
                else:
                    error = "Invalid operation."

                if error is None:
                    expression = f"{a} {op} {b}"
                    # Prepend to history
                    history.insert(0, {"expression": expression, "result": result})
                    history[:] = history[:MAX_HISTORY]
            except ValueError:
                error = "Please enter valid numbers."

    return render_template_string(
        HTML,
        num1=num1,
        num2=num2,
        op=op or "+",
        result=result,
        error=error,
        expression=expression,
        history=history,
        adv_expression=adv_expression,
        adv_result=adv_result,
        adv_error=adv_error,
        graph_url=graph_url,
        x_from=x_from,
        x_to=x_to,
        graph_requested=graph_requested,
        simul_error=simul_error,
        simul_expression=simul_expression,
        simul_result=simul_result,
        s_a=s_a,
        s_b=s_b,
        s_c=s_c,
        s_d=s_d,
        s_e=s_e,
        s_f=s_f,
    )


if __name__ == "__main__":
    app.run(debug=True)
