#!/usr/bin/env python3
"""
AutoClip MVP
============
Wani script mai sauki wanda ke:
  1. Daukar bidiyo (local file) ya fitar da audio
  2. Transcribe audio ta amfani da OpenAI Whisper API (yana gano kowanne harshe kansa)
  3. Aika transcript zuwa LLM (GPT-4o-mini ko Claude) domin ya zabi "highlights"
     (sassa masu ban sha'awa) tare da score, title, da dalili
  4. Yanke wadancan sassa daga bidiyon ta amfani da ffmpeg
  5. Fitar da sakamako a matsayin JSON + clips na mp4

Amfani:
  python autoclip_mvp.py run video.mp4 --min-score 0.7 --category default

Bukatun (requirements):
  pip install openai python-dotenv
  ffmpeg dole ya kasance a shigar (installed) a system

Environment variable:
  OPENAI_API_KEY=sk-...   (domin Whisper + LLM)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    print("Da fatan za a shigar da openai library: pip install openai", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Bayanan tsari (data structures)
# ---------------------------------------------------------------------------

@dataclass
class Clip:
    title: str
    start_time: str      # HH:MM:SS
    end_time: str        # HH:MM:SS
    score: float          # 0.0 - 1.0
    reason: str
    file: Optional[str] = None


CATEGORIES = [
    "default", "knowledge", "business", "opinion",
    "experience", "speech", "content_review", "entertainment",
]

CATEGORY_HINTS = {
    "default": "manyan abubuwa masu ban sha'awa gaba daya",
    "knowledge": "bayanai masu koyarwa, gaskiya masu amfani, ko darussa",
    "business": "shawarwarin kasuwanci, dabaru, ko lambobi masu muhimmanci",
    "opinion": "ra'ayoyi masu karfi ko sabani",
    "experience": "labaran kwarewa na sirri ko labarai masu motsa rai",
    "speech": "jawabai masu karfin gwiwa ko kalmomi masu tasiri",
    "content_review": "sharhi ko kimantawa akan wani abu (samfur, fim, littafi, da sauransu)",
    "entertainment": "wurare masu ban dariya, ban mamaki, ko motsa hankali",
}


# ---------------------------------------------------------------------------
# Mataki 1: Fitar da audio daga bidiyo
# ---------------------------------------------------------------------------

def extract_audio(video_path: Path, out_path: Path) -> Path:
    """Yana amfani da ffmpeg domin fitar da audio (mp3, 16kHz mono) daga bidiyo."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg ya kasa fitar da audio:\n{result.stderr[-1500:]}")
    return out_path


# ---------------------------------------------------------------------------
# Mataki 2: Transcribe (Whisper API) - yana gano harshe kansa
# ---------------------------------------------------------------------------

def transcribe_audio(client: OpenAI, audio_path: Path) -> dict:
    """
    Yana amfani da OpenAI Whisper API (whisper-1) domin canza audio zuwa rubutu.
    Muna neman verbose_json domin mu samu timestamps (segments).
    Whisper yana gane fiye da harshe 90 kansa - babu bukatar mu fada masa harshe.
    """
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    # transcript.segments: [{start, end, text}, ...]
    return transcript.model_dump()


def format_transcript_for_llm(transcript: dict, max_chars: int = 15000) -> str:
    """Canza segments zuwa rubutu mai layi-layi tare da timestamp, don LLM ya iya karantawa."""
    lines = []
    for seg in transcript.get("segments", []):
        start = seconds_to_hms(seg["start"])
        text = seg["text"].strip()
        lines.append(f"[{start}] {text}")
    full = "\n".join(lines)
    if len(full) > max_chars:
        # idan dogo sosai, a yanke tsakiya (samu farko da karshe, domin LLM context)
        half = max_chars // 2
        full = full[:half] + "\n...[an yanke tsakiya]...\n" + full[-half:]
    return full


def seconds_to_hms(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def hms_to_seconds(hms: str) -> float:
    parts = [float(p) for p in hms.replace(",", ".").split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


# ---------------------------------------------------------------------------
# Mataki 3: Gano highlights ta LLM
# ---------------------------------------------------------------------------

HIGHLIGHT_SYSTEM_PROMPT = """Kai kwararre ne wajen zabar sassa masu ban sha'awa (highlights) daga
rubutun bidiyo (transcript) domin a mayar da su gajerun clips na social media (TikTok/Reels/Shorts).

Za a baka transcript mai layi-layi, kowanne yana da timestamp a farko kamar haka: [HH:MM:SS] rubutu...

Aikinka:
1. Gano tsakanin 3 zuwa 8 sassa (clips) masu ban sha'awa, kowanne tsakanin 20 zuwa 90 seconds.
2. Kowanne clip dole ya zama cikakke a ma'ana (ba ya tsayawa a tsakiyar jimla).
3. Baiwa kowanne clip score daga 0.0 zuwa 1.0 (1.0 = mafi kyau/mafi ban sha'awa).
4. Baiwa kowanne clip taken (title) mai jan hankali, gajere (kasa da kalmomi 10).
5. Bada dalili guda daya a takaice (reason) domin me ya sa aka zaba wannan sashe.

Fitar da AMSA A JSON KAWAI, babu wani rubutu na daban, a wannan tsari:
{
  "clips": [
    {
      "title": "...",
      "start_time": "HH:MM:SS",
      "end_time": "HH:MM:SS",
      "score": 0.0,
      "reason": "..."
    }
  ]
}
"""


def get_highlights(client: OpenAI, transcript_text: str, category: str, model: str = "gpt-4o-mini") -> List[Clip]:
    hint = CATEGORY_HINTS.get(category, CATEGORY_HINTS["default"])
    user_prompt = (
        f"Irin abin da ake nema: {hint}\n\n"
        f"Ga transcript din:\n\n{transcript_text}"
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": HIGHLIGHT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    raw = resp.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM bai dawo da JSON mai kyau ba: {e}\nRaw: {raw[:500]}")

    clips = []
    for item in data.get("clips", []):
        clips.append(Clip(
            title=item.get("title", "Untitled"),
            start_time=item.get("start_time", "00:00:00"),
            end_time=item.get("end_time", "00:00:00"),
            score=float(item.get("score", 0.0)),
            reason=item.get("reason", ""),
        ))
    return clips


# ---------------------------------------------------------------------------
# Mataki 4: Yanke clips ta ffmpeg
# ---------------------------------------------------------------------------

def cut_clip(video_path: Path, clip: Clip, out_dir: Path, index: int) -> Path:
    start = hms_to_seconds(clip.start_time)
    end = hms_to_seconds(clip.end_time)
    duration = max(end - start, 1.0)

    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in clip.title)[:40].strip()
    safe_title = safe_title.replace(" ", "_") or f"clip{index}"
    out_file = out_dir / f"{index:02d}_{safe_title}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", str(video_path),
        "-t", str(duration),
        "-c:v", "libx264", "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        str(out_file),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg ya kasa yanke clip '{clip.title}':\n{result.stderr[-1000:]}")
    return out_file


# ---------------------------------------------------------------------------
# Babban aiki (pipeline)
# ---------------------------------------------------------------------------

def run_pipeline(
    video_path: Path,
    out_dir: Path,
    category: str = "default",
    min_score: float = 0.7,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    progress_cb=None,
) -> dict:
    """
    progress_cb: idan aka bayar, ana kiransa akai-akai kamar progress_cb(percent, stage_label)
    domin a iya nuna % da matakin aikin a frontend (misali polling daga browser).
    """
    def report(pct: int, stage: str):
        if progress_cb:
            progress_cb(min(pct, 100), stage)

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    out_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / "audio.mp3"

        report(5, "Fitar da audio daga bidiyo...")
        print("[1/4] Fitar da audio daga bidiyo...", file=sys.stderr)
        extract_audio(video_path, audio_path)

        report(15, "Transcribing (Whisper)...")
        print("[2/4] Transcribing (Whisper API, yana gano harshe kansa)...", file=sys.stderr)
        transcript = transcribe_audio(client, audio_path)
        transcript_text = format_transcript_for_llm(transcript)

        # ajiye transcript raw domin debugging/reuse
        (out_dir / "transcript.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=2))
        report(45, "An gama transcribing")

        report(50, f"Gano highlights (category={category})...")
        print(f"[3/4] Gano highlights (category={category})...", file=sys.stderr)
        all_clips = get_highlights(client, transcript_text, category, model=model)
        selected = [c for c in all_clips if c.score >= min_score]

        if not selected and min_score > 0.5:
            print(f"  Babu clip da ya kai score {min_score}, ana sake gwadawa da 0.5...", file=sys.stderr)
            selected = [c for c in all_clips if c.score >= 0.5]

        selected.sort(key=lambda c: c.score, reverse=True)
        report(70, f"An gano {len(selected)} clips, ana yankewa...")

        print(f"[4/4] Yanke {len(selected)} clips ta ffmpeg...", file=sys.stderr)
        total = max(len(selected), 1)
        for i, clip in enumerate(selected, start=1):
            clip.file = str(cut_clip(video_path, clip, clips_dir, i))
            report(70 + int(30 * i / total), f"Yanke clip {i}/{total}...")

    result = {
        "video": str(video_path),
        "category": category,
        "min_score": min_score,
        "total_candidates": len(all_clips),
        "clips": [asdict(c) for c in selected],
        "clips_dir": str(clips_dir),
    }
    (out_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    report(100, "An gama")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AutoClip MVP - yanke highlights daga bidiyo ta AI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Sarrafa bidiyo daya")
    run_p.add_argument("video", help="Path na bidiyo (local file)")
    run_p.add_argument("--out", default="./autoclip_output", help="Output directory")
    run_p.add_argument("--category", default="default", choices=CATEGORIES)
    run_p.add_argument("--min-score", type=float, default=0.7)
    run_p.add_argument("--model", default="gpt-4o-mini")
    run_p.add_argument("--api-key", default=None)
    run_p.add_argument("--json", action="store_true", help="Fitar da sakamako a matsayin JSON kawai zuwa stdout")

    args = parser.parse_args()

    if args.cmd == "run":
        video_path = Path(args.video).resolve()
        if not video_path.exists():
            print(f"Ba a samu bidiyo ba: {video_path}", file=sys.stderr)
            sys.exit(2)

        out_dir = Path(args.out).resolve()
        try:
            result = run_pipeline(
                video_path=video_path,
                out_dir=out_dir,
                category=args.category,
                min_score=args.min_score,
                model=args.model,
                api_key=args.api_key,
            )
        except Exception as e:
            print(f"Kuskure: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"\n✅ An kammala! {len(result['clips'])} clips a cikin: {result['clips_dir']}\n")
            for i, c in enumerate(result["clips"], start=1):
                print(f"  {i}. [{c['score']:.2f}] {c['title']}  ({c['start_time']} → {c['end_time']})")
                print(f"     Dalili: {c['reason']}")
                print(f"     File: {c['file']}\n")


if __name__ == "__main__":
    main()
