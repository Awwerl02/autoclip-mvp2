#!/usr/bin/env python3
"""
AutoClip - Local/Online Web Tester (mai progress bar na gaskiya)
==================================================================
Bambanci da sigar farko: yanzu sarrafa bidiyo yana faruwa a "background thread",
kuma browser yana "polling" (tambaya akai-akai) domin ganin % da matakin aikin
har sai ya kammala — maimakon jira wani "spinner" mara bayani.

Gudanarwa:
  pip install -r requirements.txt
  export OPENAI_API_KEY=sk-...
  python app.py
"""

import os
import uuid
import threading
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

# Ajiye matakin kowanne job a memory (ya isa domin MVP/gwaji guda daya-daya;
# a wani babban tsari na gaba, za a canza zuwa Redis/database domin
# yin aiki daidai ko da server ya sake gudana ko akwai instance da yawa).
JOBS = {}
JOBS_LOCK = threading.Lock()


def set_job(job_id, **fields):
    with JOBS_LOCK:
        JOBS[job_id].update(fields)


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/start", methods=["POST"])
def start_job():
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

    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "queued",
            "progress": 0,
            "stage": "A layi...",
            "result": None,
            "error": None,
        }

    def worker():
        set_job(job_id, status="processing", progress=1, stage="An fara...")

        def on_progress(pct, stage):
            set_job(job_id, progress=pct, stage=stage)

        job_out_dir = OUTPUT_DIR / job_id
        try:
            result = run_pipeline(
                video_path=saved_video_path,
                out_dir=job_out_dir,
                category=category,
                min_score=min_score,
                api_key=api_key,
                progress_cb=on_progress,
            )
            for c in result["clips"]:
                filename = Path(c["file"]).name
                c["url"] = f"/clips/{job_id}/{filename}"
            set_job(job_id, status="done", progress=100, stage="An gama", result=result)
        except Exception as e:
            traceback.print_exc()
            set_job(job_id, status="error", error=str(e))

    threading.Thread(target=worker, daemon=True).start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Ba a samu wannan job ba."}), 404
    return jsonify(job)


@app.route("/clips/<job_id>/<path:filename>")
def serve_clip(job_id, filename):
    clips_dir = OUTPUT_DIR / job_id / "clips"
    return send_from_directory(clips_dir, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Uploads: {UPLOAD_DIR}")
    print(f"Output:  {OUTPUT_DIR}")
    print(f"Ana gudana akan port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
