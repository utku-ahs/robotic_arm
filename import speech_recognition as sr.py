import requests
import speech_recognition as sr
import pyttsx3
import time

# ===================== LOCAL LLM (OLLAMA) =====================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

SYSTEM_PROMPT = (
    "You are Jarvis. You are sharp, sarcastic, and slightly rude. "
    "You keep responses short, usually one sentence. "
    "You are blunt and dry. No comfort, no therapy."
)

def ask_llm(prompt, memory_context=""):
    payload = {
        "model": MODEL,
        "prompt": (
            SYSTEM_PROMPT
            + "\n\nContext:\n"
            + memory_context
            + "\n\nUser: "
            + prompt
            + "\nJarvis:"
        ),
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["response"].strip()

# ===================== MEMORY =====================
def build_memory_context():
    return (
        "Ahsen went to New York. "
        "The user fell in love with her. "
        "She never came back."
    )

# ===================== NAME FIX =====================
def normalize_text(text):
    corrections = {
        "austin": "ahsen",
        "arsen": "ahsen",
        "aschen": "ahsen",
        "ah son": "ahsen"
    }
    return " ".join(corrections.get(w, w) for w in text.lower().split())

# ===================== VOICE =====================
tts = pyttsx3.init()
voices = tts.getProperty("voices")

voice_id = voices[0].id
for v in voices:
    if "david" in v.name.lower() or "male" in v.name.lower():
        voice_id = v.id
        break

tts.setProperty("voice", voice_id)
tts.setProperty("rate", 150)

def speak(text):
    print(f"[JARVIS]: {text}")
    tts.say(text)
    tts.runAndWait()
    time.sleep(0.1)  # prevents Windows audio lock

# ===================== OVERRIDES =====================
def emotional_override(text):
    if "she came back" in text or "ahsen came back" in text:
        return "No, she didn’t. If she had, you wouldn’t be guessing."

    if "ahsen is here" in text:
        return "If she were here, you wouldn’t be talking to me."

    return None

# ===================== SPEECH INPUT =====================
recognizer = sr.Recognizer()
mic = sr.Microphone()

speak("Yeah. I'm here. Talk.")

# ===================== MAIN LOOP =====================
while True:
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            print("\n🎙️ Listening...")
            audio = recognizer.listen(source)

        try:
            raw = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            speak("That was noise. Try again.")
            continue

        text = normalize_text(raw)
        print(f"[YOU]: {text}")

        # 🔥 OVERRIDE PATH — NOW SPEAKS
        forced = emotional_override(text)
        if forced:
            speak(forced)
            continue

        # NORMAL AI RESPONSE
        try:
            reply = ask_llm(text, build_memory_context())
        except Exception:
            speak("I’m not thinking right now.")
            continue

        speak(reply)

    except KeyboardInterrupt:
        speak("Finally. Silence.")
        break
