"""Personal Voice Assistant.

Uses SpeechRecognition for speech-to-text (Google Web Speech API) and
gTTS (Google Text-to-Speech) for spoken responses. Also supports a cloned
"strife" voice via Coqui XTTS-v2 using voices/strife_raw.wav as reference.

Run:
    python assistant.py                    # voice mode (requires a microphone)
    python assistant.py --text             # text mode (type commands instead)
    python assistant.py --voice strife     # speak with the cloned Strife voice
"""

import argparse
import datetime
import os
import subprocess
import sys
import tempfile
import webbrowser

import pyjokes
import speech_recognition as sr
import wikipedia
from gtts import gTTS

ASSISTANT_NAME = "Strife"
VOICE = "strife"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STRIFE_REF_WAV = os.path.join(BASE_DIR, "voices", "strife_raw.wav")
_xtts = None
wikipedia.set_user_agent("PersonalVoiceAssistant/1.0 (personal use)")
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.txt")


def _get_xtts():
    """Lazily load the XTTS-v2 voice-cloning model."""
    global _xtts
    if _xtts is None:
        os.environ.setdefault("COQUI_TOS_AGREED", "1")
        from TTS.api import TTS
        print("(loading Strife voice model, this may take a minute...)")
        _xtts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
    return _xtts


def speak(text: str) -> None:
    """Speak the given text aloud with the selected voice."""
    print(f"{ASSISTANT_NAME}: {text}")
    try:
        if VOICE == "strife":
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                path = f.name
            _get_xtts().tts_to_file(
                text=text, speaker_wav=STRIFE_REF_WAV, language="en", file_path=path
            )
        else:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                path = f.name
            gTTS(text=text, lang="en").save(path)
        for player in (["mpg123", "-q", path], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]):
            try:
                subprocess.run(player, check=True)
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        os.remove(path)
    except Exception as e:
        print(f"(TTS unavailable: {e})")


def listen(recognizer: sr.Recognizer) -> str:
    """Listen on the microphone and return recognized text (lowercased)."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You: {text}")
        return text.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
    except sr.RequestError:
        speak("Speech service is unavailable right now.")
    return ""


def take_note(command: str) -> None:
    note = command.replace("take a note", "").replace("note down", "").strip()
    if not note:
        speak("What should I note down?")
        return
    with open(NOTES_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {note}\n")
    speak("Noted.")


def read_notes() -> None:
    if not os.path.exists(NOTES_FILE):
        speak("You have no notes yet.")
        return
    with open(NOTES_FILE) as f:
        notes = f.read().strip()
    speak("Here are your notes. " + notes if notes else "You have no notes yet.")


def handle(command: str) -> bool:
    """Handle a command. Returns False when the assistant should exit."""
    if not command:
        return True

    if any(w in command for w in ("exit", "quit", "goodbye", "stop")):
        speak("Goodbye! Have a great day.")
        return False
    elif "time" in command:
        speak(f"The time is {datetime.datetime.now():%I:%M %p}.")
    elif "date" in command or "day" in command:
        speak(f"Today is {datetime.datetime.now():%A, %B %d, %Y}.")
    elif "wikipedia" in command or command.startswith(("who is", "what is")):
        query = (
            command.replace("wikipedia", "")
            .replace("search", "")
            .replace("who is", "")
            .replace("what is", "")
            .strip()
        )
        if not query:
            speak("What should I look up?")
            return True
        try:
            speak(wikipedia.summary(query, sentences=2, auto_suggest=False))
        except Exception:
            try:
                results = wikipedia.search(query)
                speak(wikipedia.summary(results[0], sentences=2, auto_suggest=False))
            except Exception:
                speak(f"I couldn't find anything about {query}.")
    elif "open youtube" in command:
        speak("Opening YouTube.")
        webbrowser.open("https://youtube.com")
    elif "open google" in command:
        speak("Opening Google.")
        webbrowser.open("https://google.com")
    elif "search for" in command:
        query = command.split("search for", 1)[1].strip()
        speak(f"Searching the web for {query}.")
        webbrowser.open(f"https://www.google.com/search?q={query}")
    elif "joke" in command:
        speak(pyjokes.get_joke())
    elif "take a note" in command or "note down" in command:
        take_note(command)
    elif "read" in command and "note" in command:
        read_notes()
    elif "your name" in command:
        speak(f"I'm {ASSISTANT_NAME}, your personal voice assistant.")
    elif "hello" in command or "hi" in command:
        speak(f"Hello! How can I help you?")
    elif "help" in command or "what can you do" in command:
        speak(
            "You can ask me the time or date, search Wikipedia, open YouTube or "
            "Google, search the web, take and read notes, or tell a joke. "
            "Say goodbye to exit."
        )
    else:
        speak("Sorry, I don't know that one yet. Say help to hear what I can do.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal voice assistant")
    parser.add_argument("--text", action="store_true", help="type commands instead of speaking")
    parser.add_argument("--voice", choices=["google", "strife"], default="strife",
                        help="TTS voice: strife (cloned via XTTS-v2) or google (gTTS)")
    args = parser.parse_args()

    global VOICE
    VOICE = args.voice

    speak(f"Hi, I'm {ASSISTANT_NAME}. How can I help you today?")

    if args.text:
        while True:
            try:
                command = input("You: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not handle(command):
                break
    else:
        recognizer = sr.Recognizer()
        try:
            sr.Microphone()
        except OSError:
            print("No microphone found. Falling back to text mode (or run with --text).")
            sys.exit(main_text())
        while True:
            try:
                command = listen(recognizer)
            except sr.WaitTimeoutError:
                continue
            except KeyboardInterrupt:
                break
            if not handle(command):
                break


def main_text() -> int:
    while True:
        try:
            command = input("You: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not handle(command):
            return 0


if __name__ == "__main__":
    main()
