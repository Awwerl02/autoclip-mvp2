#!/usr/bin/env python3
"""
AutoClip - Local Web Tester
============================
Wani karamin Flask server domin gwada autoclip_mvp.py ta browser (Chrome)
maimakon gudanar da CLI a terminal a kowanne lokaci.

MUHIMMI: OpenAI API ba ta bada izinin kira kai-tsaye daga browser (CORS) ba,
don haka wani gaba-daya-static HTML file (misali file:// da za a bude kai-tsaye)
BA ZAI YI AIKI BA idan ya kira OpenAI kansa. Saboda haka, wannan karamin
server (wanda ke gudana a kwamfutarka, ba a intanet ba) shi ke kiran OpenAI,
sannan browser din kawai yana magana da wannan local server.

Gudanarwa:
  pip install -r requirements.txt
  export OPENAI_API_KEY=sk-...      (ko ka shigar da key a form din a browser)
  python app.py
  sannan bude http://localhost:5000 a Chrome
"""

import os
import uuid
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory

from autoclip_mvp import run_pipeline, CATEGORIES

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "web_output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_MB = 500

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/process", methods=["POST"])
def process():
    video_file = request.files.get("video")
    if not video_file or video_file.filename == "":
        return jsonify({"error": "Ba a zaba bidiyo ba."}), 400

    category = request.form.get("category", "default")
    try:
        min_score = float(request.form.get("min_score", 0.7))
    except ValueError:
        min_score = 0.7

    api_key = request.form.get("api_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "error": "Babu OpenAI API key. Shigar da shi a form din, ko saita OPENAI_API_KEY kafin gudanar da server."
        }), 400

    job_id = uuid.uuid4().hex[:12]
    ext = Path(video_file.filename).suffix or ".mp4"
    saved_video_path = UPLOAD_DIR / f"{job_id}{ext}"
    video_file.save(saved_video_path)

    job_out_dir = OUTPUT_DIR / job_id

    try:
        result = run_pipeline(
            video_path=saved_video_path,
            out_dir=job_out_dir,
            category=category,
            min_score=min_score,
            api_key=api_key,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    # mayar da file paths zuwa URLs domin browser ya iya kunnawa/download
    for c in result["clips"]:
        filename = Path(c["file"]).name
        c["url"] = f"/clips/{job_id}/{filename}"

    return jsonify(result)


@app.route("/clips/<job_id>/<path:filename>")
def serve_clip(job_id, filename):
    clips_dir = OUTPUT_DIR / job_id / "clips"
    return send_from_directory(clips_dir, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Uploads: {UPLOAD_DIR}")
    print(f"Output:  {OUTPUT_DIR}")
    print(f"Ana gudana akan port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
