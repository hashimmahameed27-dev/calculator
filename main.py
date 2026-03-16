from flask import Flask, request, render_template_string

app = Flask(__name__)

# Simple in-memory history for this server process
history = []
MAX_HISTORY = 20


HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Calculator • Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      :root {
        --bg: #0f172a;
        --bg-card: #020617;
        --border-subtle: rgba(148, 163, 184, 0.25);
        --accent: #6366f1;
        --accent-soft: rgba(99, 102, 241, 0.18);
        --accent-strong: #4f46e5;
        --text: #e5e7eb;
        --text-muted: #9ca3af;
        --danger: #f97373;
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
        background: radial-gradient(circle at top, #1f2937, #020617);
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
        background: radial-gradient(circle at top left, rgba(148, 163, 184, 0.25), transparent 55%),
                    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.25), transparent 55%),
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
        background: radial-gradient(circle at top right, rgba(129, 140, 248, 0.22), transparent 60%),
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
        border: 1px solid rgba(129, 140, 248, 0.5);
        color: #c7d2fe;
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
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(30, 64, 175, 0.65);
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
        background: rgba(15, 23, 42, 0.8);
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
          0 10px 22px rgba(79, 70, 229, 0.55),
          0 0 0 1px rgba(129, 140, 248, 0.85);
        transition: transform 0.08s ease, box-shadow 0.08s ease, filter 0.08s ease;
      }

      button:hover {
        filter: brightness(1.06);
        box-shadow:
          0 14px 28px rgba(79, 70, 229, 0.65),
          0 0 0 1px rgba(129, 140, 248, 0.95);
      }

      button:active {
        transform: translateY(1px);
        box-shadow:
          0 9px 18px rgba(79, 70, 229, 0.45),
          0 0 0 1px rgba(129, 140, 248, 0.8);
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
        border-color: rgba(248, 113, 113, 0.7);
        background: rgba(127, 29, 29, 0.35);
        color: #fecaca;
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

    if request.method == "POST":
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
                history = history[:MAX_HISTORY]
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
    )


if __name__ == "__main__":
    app.run(debug=True)
