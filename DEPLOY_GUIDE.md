# Jagorar Deploy — Daga Waya Kai Tsaye (babu bukatar kwamfuta)

Wannan jagora zai taimaka maka ka sanya AutoClip MVP a kan intanet (online), sannan ka gwada shi ta hanyar bude link a Chrome a wayarka — daidai kamar yadda za ka bude kowanne website.

Za mu yi amfani da:
- **GitHub** — wurin ajiye code din (kyauta)
- **Render.com** — wurin da zai gudanar da code din a intanet (kyauta don gwaji, akwai iyaka)

---

## Mataki 1: Kirkiri GitHub account

1. Bude https://github.com a Chrome, latsa "Sign up"
2. Kirkiri account (email + password)

## Mataki 2: Kirkiri sabon repository

1. Bayan ka shiga (login), latsa "+" a sama dama, sannan "New repository"
2. Baiwa suna: `autoclip-mvp`
3. Zaba **Public** (ko Private, dukkanin za su yi aiki da Render kyauta)
4. Kar ka zaba "Add a README file" (mu na da namu)
5. Latsa "Create repository"

## Mataki 3: Loda fayilolin (upload) — babu bukatar git command

**MUHIMMI:** wannan mataki dole a yi shi ta **Chrome (browser)** akan **github.com**, ba GitHub app din da aka girka ba — GitHub app baya bada damar loda fayiloli da yawa lokaci guda.

1. A Chrome, bude github.com, tabbatar ka shiga (logged in)
2. Je shafin repository dinka (`autoclip-mvp`)
3. Latsa "Add file" → "Upload files"
4. Latsa wurin da za a zaba fayiloli (ko "choose your files") — zai bude file manager na wayarka
5. Je Downloads (ko inda ka ajiye fayilolin da na baka), **zaba dukkan fayilolin nan** (duk suna a fadin folder guda, babu subfolder yanzu):
   - `app.py`
   - `autoclip_mvp.py`
   - `index.html`
   - `requirements.txt`
   - `Dockerfile`
   - `.gitignore`
   - `README.md`
   - (DEPLOY_GUIDE.md idan kana so)
6. Bayan an loda su duka, gungura kasa, rubuta sako a "Commit message" (misali "Farkon fayiloli")
7. Latsa "Commit changes"

## Mataki 4: Kirkiri Render account, kuma hada shi da GitHub

1. Bude https://render.com a Chrome, latsa "Get Started", zaba "Sign up with GitHub"
2. Baiwa Render izini (authorize) ya ga repositories dinka

## Mataki 5: Kirkiri "Web Service" akan Render

1. A Render dashboard, latsa "New +" → "Web Service"
2. Zaba repository dinka (`autoclip-mvp`)
3. Render zai gane `Dockerfile` din kansa — zaba **"Docker"** a matsayin Environment (idan ya tambaya)
4. Baiwa suna (misali `autoclip-mvp`)
5. **Instance Type**: zaba "Free"
6. A sashen **Environment Variables**, latsa "Add Environment Variable":
   - Key: `OPENAI_API_KEY`
   - Value: `sk-...` (naka OpenAI API key)
7. Latsa "Create Web Service"

## Mataki 6: Jira (build) — sannan gwada

1. Render zai fara "building" — zai dauki 'yan mintuna (yana shigar da ffmpeg da Python packages)
2. Idan ya gama, za ka ga wani URL a sama kamar: `https://autoclip-mvp-xxxx.onrender.com`
3. Latsa/kwafa wannan URL, bude shi a Chrome — za ka ga fuskar AutoClip!
4. Loda wani gajeren bidiyo (misali kasa da minti 2 don gwaji na farko), latsa "Fara sarrafa bidiyo"

---

## Muhimman bayanai

- **Free tier na Render** yana "barci" (sleep) idan babu wanda ya yi amfani da shi na wani lokaci — buɗewa ta farko bayan barci na iya daukar dakika 30-60 kafin ya farka. Wannan al'ada ce, ba kuskure ba.
- **Bidiyo mai girma** (dogo sosai ko babban file) na iya daukar lokaci mai tsawo ko ya kasa akan free tier saboda karancin RAM/CPU — fara da gajerun bidiyo (1-3 min) domin gwaji.
- Idan Render ya nuna "Build failed", latsa "Logs" domin ganin ainihin kuskuren, sannan kwafa mani sakon domin mu gyara.
- Idan a wani lokaci ka canza wani abu a code din (misali `HIGHLIGHT_SYSTEM_PROMPT` a `autoclip_mvp.py`), sai ka je GitHub, ka gyara file din a can kai tsaye (latsa alamar fensir/pencil a file din), ka "Commit changes" — Render zai gane kansa ya sake "deploy" ta atomatik.

---

## Idan kana son gwadawa gaba daya a wayarka (offline, ba tare da online hosting ba)

Akwai wata hanya ta amfani da **Termux** (wani app na terminal a Android) domin girka Python + ffmpeg kai tsaye a wayarka. Wannan yana da wahala kadan kuma yana bukatar sarari (storage) da RAM. In kana son wannan hanyar maimakon, gaya mani, zan baka jagora dabam.
