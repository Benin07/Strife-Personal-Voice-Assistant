# Strife — Personal Voice Assistant

A Python voice assistant using **SpeechRecognition** (Google Web Speech API) for
speech-to-text. Replies are spoken in a cloned **Strife** voice (Coqui XTTS-v2,
cloned from `voices/strife_raw.wav`), with **gTTS** available as a fallback voice.

## Features
- Tell the current time and date
- Wikipedia lookups ("who is Alan Turing", "wikipedia python")
- Open YouTube / Google, web search ("search for weather in London")
- Take and read back notes
- Tell jokes

## Setup

```bash
# system deps (Linux)
sudo apt-get install portaudio19-dev python3-dev mpg123

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python assistant.py                   # voice mode (needs a microphone), Strife voice
python assistant.py --text            # text mode (type commands)
python assistant.py --voice google    # use the plain gTTS voice instead
```

The first run with the Strife voice downloads the XTTS-v2 model (~2 GB).
On CPU, each reply takes a few seconds to synthesize.

Say "help" to hear available commands and "goodbye" to exit.
