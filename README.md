# AutoClip MVP

Sauki, kwatankwacin script domin gwada ainihin tsarin AutoClip kafin gina cikakken website:

**Bidiyo → Audio → Whisper transcript (kowanne harshe) → LLM ya zabi highlights → FFmpeg ya yanke clips**

## Shigarwa (Setup)

1. **FFmpeg** dole ya kasance a shigar a kwamfutarka:
   ```bash
   # Mac
   brew install ffmpeg
   # Ubuntu/Debian
   sudo apt install ffmpeg
   # Windows: sauke daga https://ffmpeg.org/download.html sannan a kara zuwa PATH
   ```

2. Shigar da Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Saita OpenAI API key dinka (samu a https://platform.openai.com/api-keys):
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

## Zabi 1: Local Web UI (mafi sauki don gwaji — bude a Chrome)

Maimakon rubuta commands a terminal kowanne lokaci, akwai wani karamin **local web page** domin ka loda bidiyo ka duba/download clips kai-tsaye a Chrome:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python app.py
```

Sannan bude **http://localhost:5000** a Chrome. Za ka ga form: zaba bidiyo, zaba category, sannan latsa "Fara sarrafa bidiyo". Bayan an gama, za a nuna clips a can — kana iya kallonsu (video preview) ko download kai tsaye.

> ⚠️ **Muhimmin bayani:** ba a iya yin wani file na HTML **kai-tsaye** (misali wanda za ka bude ta double-click, `file://...`) wanda ke kiran OpenAI API daga browser kai-tsaye — OpenAI baya bada CORS izini domin haka, kuma za a nuna API key dinka a fili ga duk wanda ya bude "View Source". Saboda haka `app.py` (Flask) yana zama karamin server a **kwamfutarka kanta** (ba a intanet ba) wanda ke kira OpenAI, sannan browser dinka kawai yake magana da wannan local server — wannan shi ne mafi sauki hanya mai aminci domin gwaji ta browser.

## Zabi 2: CLI (domin scripting/automation ko idan kana son JSON output)

```bash
python autoclip_mvp.py run talk.mp4
```

Zabuka (options):

```bash
# Zaba category domin taimakawa LLM ya fahimci irin bidiyo
python autoclip_mvp.py run talk.mp4 --category business

# Rage score domin samun clips da yawa (default 0.7)
python autoclip_mvp.py run talk.mp4 --min-score 0.5

# Saita wurin ajiye sakamako
python autoclip_mvp.py run talk.mp4 --out ./output_talk1

# Fitar da sakamako a JSON kawai (don amfani a wani script/API)
python autoclip_mvp.py run talk.mp4 --json
```

## Fayilolin da ke cikin project din — me kowanne ke yi

```
autoclip-mvp/
├── autoclip_mvp.py     # Ainihin "injin" (pipeline): extract audio → transcribe → highlights → cut clips
├── app.py              # Flask server — yana amfani da autoclip_mvp.py, yana ba shi fuska (UI) a browser
├── templates/
│   └── index.html      # Fuskar da za ka gani a Chrome (form + jerin clips)
├── requirements.txt
└── README.md
```

`app.py` **baya sake rubuta** pipeline din — yana kawai `import`-ing `run_pipeline()` daga `autoclip_mvp.py` ya kira shi lokacin da wani ya loda bidiyo. Wannan yana nufin:
- Duk canjin da ka yi a `autoclip_mvp.py` (misali sabon category, ko canza yadda ake zabar highlights) **zai yi aiki ta CLI da web UI duka biyu** ba tare da ka canza su daban ba.
- Idan kana son gwada canji da sauri, yi shi ta CLI (`python autoclip_mvp.py run ...`) domin sauri (babu bukatar sake budawa Chrome/server).

### Muhimman wurare a `autoclip_mvp.py` da za ka iya canzawa da farko:

| Aiki (function) | Me ya ke yi | Idan kana son canza shi |
|---|---|---|
| `extract_audio()` | Fitar da audio daga bidiyo | Canza codec/quality na audio |
| `transcribe_audio()` | Whisper API call | Idan kana son amfani da wani transcription service daban |
| `HIGHLIGHT_SYSTEM_PROMPT` | Umarnin da ake baiwa LLM domin zabar highlights | **Nan ne wurin da za ka fi gyarawa** — canza yaren prompt, tsawon clips (yanzu 20–90s), adadin clips (yanzu 3–8) |
| `get_highlights()` | Kiran LLM, sarrafa amsarsa | Canza `model=` zuwa wani LLM daban (misali GPT-4o don ingantacce amma tsada) |
| `cut_clip()` | ffmpeg command na yankewa | Nan za ka kara vertical export (9:16) da captions daga baya |
| `run_pipeline()` | Ya hada dukkan matakan sama | Nan za ka iya kara sabon mataki (misali "vertical export" bayan `cut_clip`) |

### Yadda za ka gwada sauyi cikin sauki

1. Bude `autoclip_mvp.py` a wani editor (VS Code shine mafi kyau — kyauta ne, `code .` a terminal)
2. Yi canjinka (misali canza `HIGHLIGHT_SYSTEM_PROMPT`)
3. Gwada nan take ta CLI: `python autoclip_mvp.py run short_test.mp4 --json`
4. Idan ya yi aiki daidai, sabunta browser (http://localhost:5000) idan `app.py` yana gudana — Flask yana da `debug=True` don haka zai sake loda code din kansa

## Abin da za ka samu

```
autoclip_output/
├── transcript.json     # cikakken transcript daga Whisper (tare da timestamps)
├── result.json          # jerin clips da aka zaba, tare da score/title/reason
└── clips/
    ├── 01_Wani_Taken.mp4
    ├── 02_Wani_Taken.mp4
    └── ...
```

## Menene mataki na gaba (bayan wannan MVP ya yi aiki)?

1. **Sanya cikin FastAPI backend** — maimakon CLI, ka mayar da `run_pipeline()` zuwa wani API endpoint (`POST /clip`) domin website ka iya kiran shi.
2. **Async job queue** — bidiyo na iya daukar lokaci; yi amfani da Celery/RQ/BullMQ domin process a background, sannan frontend ya yi polling na status (kamar `get_job_status` a AutoClip).
3. **Cloud storage** — ajiye bidiyo/clips a S3 ko Cloudflare R2 maimakon local disk.
4. **Vertical export (9:16) + burned-in captions** — kara wani mataki bayan `cut_clip()` wanda ke amfani da ffmpeg `crop`/`scale` filters tare da ASS/SRT subtitles domin TikTok/Reels/Shorts.
5. **Frontend (Next.js)** — form domin loda bidiyo/link (yt-dlp domin YouTube/Twitch links), progress bar, da preview na clips.
6. **Stripe/crypto payment** — takaita free users (misali max 10 min bidiyo/wata), bude duk domin premium.
