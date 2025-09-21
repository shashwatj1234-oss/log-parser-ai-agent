# app.py
import json
import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils import ParserUtil, LogFilter

app = Flask(__name__)
CORS(app)

SONAR_API_URL = "https://api.perplexity.ai/chat/completions"
SONAR_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
SONAR_API_KEY = os.getenv("PERPLEXITY_API_KEY")


def build_llm_messages(prompt: str, filtered_logs):
    subset = filtered_logs[:120]
    lines = []
    for r in subset:
        idx = r.get("_idx", 0)
        container = r.get("containerName") or r.get("podName") or "unknown"
        logline = str(r.get("log", ""))[:800]
        lines.append(f"[{idx}] {container} | {logline}")

    logs_text = "\n".join(lines)
    system = (
        "You are an incident triage assistant. "
        "Given a user incident prompt and recent logs, identify which log lines are most relevant. "
        "Return ONLY a JSON object with fields: "
        "{\"summary\": string, \"relevant_log_indices\": number[], \"reason\": string}. "
        "Do not include any other text."
    )
    user = f"Incident: {prompt}\n\nLogs:\n{logs_text}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def analyze_logs_with_llm(filtered_logs, prompt):
    messages = build_llm_messages(prompt, filtered_logs)
    headers = {
        "Authorization": f"Bearer {SONAR_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SONAR_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
    }
    resp = requests.post(SONAR_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Get content and usage
    content = ""
    if data.get("choices"):
        content = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage", {}) or {}

    # Parse JSON returned by the model
    try:
        analysis = json.loads(content)
    except Exception:
        # lenient fallback: try to snip a JSON object from content
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                analysis = json.loads(m.group(0))
            except Exception:
                analysis = {"summary": content.strip(), "relevant_log_indices": [], "reason": "LLM returned non-JSON."}
        else:
            analysis = {"summary": content.strip(), "relevant_log_indices": [], "reason": "LLM returned plain text."}

    # Build highlights list from indices
    idx_set = set()
    for v in analysis.get("relevant_log_indices", []):
        try:
            idx_set.add(int(v))
        except Exception:
            pass

    highlighted = [r for r in filtered_logs if int(r.get("_idx", -1)) in idx_set]
    return {
        "summary": analysis.get("summary", ""),
        "reason": analysis.get("reason", ""),
        "relevant_log_indices": sorted(list(idx_set)),
        "highlighted": highlighted,
        "usage": usage,
        "model": data.get("model", SONAR_MODEL),
    }


# --- Route ---

@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "debug": app.debug,
        "has_key": bool(SONAR_API_KEY),
        "model": SONAR_MODEL
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    if not SONAR_API_KEY:
        return jsonify({"error": "Server missing PERPLEXITY_API_KEY env var."}), 400

    file = request.files.get("file")
    prompt = request.form.get("prompt", "")

    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded."}), 400

    try:
        parsed_log = ParserUtil.parse_ndjson_content(file.read())

        filtered = LogFilter.filter_logs(parsed_log, prompt)
        result = analyze_logs_with_llm(filtered, prompt)

        return jsonify({
            "counts": {
                "total_records": len(parsed_log),
                "filtered_records": len(filtered),
                "highlighted_records": len(result["highlighted"]),
            },
            "summary": result["summary"],
            "reason": result["reason"],
            "highlighted": result["highlighted"],
            "usage": result["usage"],
            "model": result["model"],
        })
    except requests.HTTPError as e:
        return jsonify(
            {"error": "Perplexity API error", "details": str(e), "body": getattr(e.response, "text", "")}), 502
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


if __name__ == "__main__":
    # Use port 8000 to match the frontend defaults
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False, threaded=False)

