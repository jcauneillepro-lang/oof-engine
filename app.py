"""
OOF Engine — Flask backend
Three endpoints:
  POST /api/generate        → source text → HTML brief (calls Claude)
  POST /api/export/pdf      → HTML brief → PDF binary
  POST /api/export/pptx     → HTML brief → PPTX binary

Frontend (static) is served from /frontend.
"""
import os
from io import BytesIO
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from claude_engine import generate_brief
from pptx_export import html_to_pptx, html_to_pdf


FRONTEND_DIR = Path(__file__).parent

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)  # so the frontend can talk to the API from any origin (dev convenience)


# ============================================================
# STATIC FRONTEND
# ============================================================

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_assets(path):
    return send_from_directory(FRONTEND_DIR, path)


# ============================================================
# API · GENERATE
# Accepts: { "source": "...", "constraint": "..." (optional) }
# Returns: { "html": "<!DOCTYPE html>..." }
# ============================================================

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}
    source = (data.get("source") or "").strip()
    constraint = (data.get("constraint") or "").strip()

    if not source:
        # Empty source → use a starter
        source = (
            "Build me a starter v23 brief — 4 slides. "
            "Cover, a hero number, a SO WHAT slide, and a closer. "
            "Use NACO Pulse as the example topic with placeholder content."
        )

    try:
        html = generate_brief(source, constraint)
        return jsonify({"html": html, "len": len(html)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# API · EXPORT PDF
# Accepts: { "html": "..." }
# Returns: PDF binary (download)
# ============================================================

@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    data = request.get_json(silent=True) or {}
    html = data.get("html")
    if not html:
        return jsonify({"error": "no html provided"}), 400
    try:
        pdf = html_to_pdf(html)
        return send_file(
            BytesIO(pdf), mimetype="application/pdf",
            as_attachment=True, download_name="OOF_brief.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# API · EXPORT PPTX
# Accepts: { "html": "..." }
# Returns: PPTX binary (download)
# ============================================================

@app.route("/api/export/pptx", methods=["POST"])
def api_export_pptx():
    data = request.get_json(silent=True) or {}
    html = data.get("html")
    if not html:
        return jsonify({"error": "no html provided"}), 400
    try:
        pptx = html_to_pptx(html)
        return send_file(
            BytesIO(pptx),
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True, download_name="OOF_brief.pptx"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health")
def health():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return jsonify({"ok": True, "claude_configured": has_key})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
