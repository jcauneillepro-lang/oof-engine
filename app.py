"""
OOF Engine — Flask backend
Endpoints:
  POST /api/upload          → binary file (.pptx/.docx/.pdf/.txt/.md/.csv/.json) → extracted text
  POST /api/generate        → source text → HTML brief (calls Claude)
  POST /api/export/pdf      → HTML brief → PDF binary
  POST /api/export/pptx     → HTML brief → PPTX binary
  GET  /api/health          → liveness check

Frontend (static) is served from the same directory.
"""
import os
from io import BytesIO
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from claude_engine import generate_brief
from pptx_export import html_to_pptx, html_to_pdf
from file_parser import extract_text
from engine_audit import audit_brief, lint_brief


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
    archetype = (data.get("archetype") or "auto").strip()
    audience = (data.get("audience") or "auto").strip()
    slide_count = (data.get("slide_count") or "auto").strip()
    cover_style = (data.get("cover_style") or "auto").strip()
    divider_style = (data.get("divider_style") or "auto").strip()

    if not source:
        source = (
            "Build me a starter v23 brief — 4 slides. "
            "Cover, a hero number, a SO WHAT slide, and a closer. "
            "Use NACO Pulse as the example topic with placeholder content."
        )

    # Audit toggle — default ON; skip with ?audit=false or audit:false in body
    audit_param = (data.get("audit", request.args.get("audit", "true")))
    run_audit = str(audit_param).lower() != "false"
    skip_critic = str(data.get("skip_critic", request.args.get("skip_critic", "false"))).lower() == "true"

    try:
        html = generate_brief(
            source=source,
            constraint=constraint,
            archetype=archetype,
            audience=audience,
            slide_count=slide_count,
            cover_style=cover_style,
            divider_style=divider_style,
        )

        response_payload = {"html": html, "len": len(html)}

        if run_audit:
            try:
                audit = audit_brief(html, source=source, skip_critic=skip_critic)
                response_payload["audit"] = audit
            except Exception as audit_err:
                response_payload["audit"] = {"error": f"audit failed: {audit_err}"}

        return jsonify(response_payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# API · AUDIT (standalone — re-audit existing brief HTML)
# Accepts: { "html": "...", "source": "..." (optional), "skip_critic": false }
# Returns: { "audit": {...} }
# ============================================================

@app.route("/api/audit", methods=["POST"])
def api_audit():
    data = request.get_json(silent=True) or {}
    html = data.get("html", "")
    source = data.get("source", "")
    skip_critic = bool(data.get("skip_critic", False))
    if not html:
        return jsonify({"error": "no html provided"}), 400
    try:
        audit = audit_brief(html, source=source, skip_critic=skip_critic)
        return jsonify({"audit": audit})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# API · UPLOAD (binary files → extracted text)
# Accepts multipart/form-data with field `file`.
# Returns: { "text": "...", "filename": "...", "chars": N }
# ============================================================

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "no file in request"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "empty filename"}), 400
    try:
        text = extract_text(f.filename, f.read())
        return jsonify({
            "text": text,
            "filename": f.filename,
            "chars": len(text),
        })
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
