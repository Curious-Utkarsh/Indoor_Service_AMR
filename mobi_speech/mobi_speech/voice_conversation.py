#!/usr/bin/env python3

import whisper #For processing and converting to text the recorded sound
import sounddevice as sd #For Capturing or recording sound
from gtts import gTTS #for coverting text to speech
import os #to join paths
import google.generativeai as genai #sending prompts text/video/image
import time #waiting time for recording 
from playsound import playsound #to play the speech output by gTTS
from scipy.io.wavfile import write #to write .wav file

# Define base directory for storing audio files
BASE_PATH = "/home/utk/mobi_ws/src/mobi_speech/output_voice"  # Modify this as needed
os.makedirs(BASE_PATH, exist_ok=True)

# Load Whisper model
print("Loading Whisper model...")
model = whisper.load_model("base")  # Try "tiny" if you're on low resources
print("Whisper model ready")

# Gemini API setup
GEN_API_KEY = 'AIzaSyCxNXoKqtpn-ClgABBgxSPe9ZkDSVBWuMU'
genai.configure(api_key=GEN_API_KEY)
gemini = genai.GenerativeModel('gemini-2.0-flash')

# Voice Input
def get_voice_input():
    print("Speak now...")
    fs = 16000
    duration = 3

    # Record audio
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # Save audio to file
    wav_path = os.path.join(BASE_PATH, "input.wav")
    write(wav_path, fs, audio)

    print("Processing with Whisper...")
    result = model.transcribe(wav_path)
    print("You said:", result["text"])
    return result["text"]

# Gemini response
def get_gemini_response(prompt):
    personality = (
        "You are a helpful friendly robot assistant. "
        "Keep responses simple, polite, and homourous. "
        "Avoid punctuation and use of emoji. "
    )

    final_prompt = f"{personality}\n\nHuman: {prompt}\nRobot:"

    try:
        response = gemini.generate_content(final_prompt)
        return response.text
    except Exception as e:
        print("Error with Gemini:", e)
        return "Sorry I cannot respond"

# Speak using gTTS
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = os.path.join(BASE_PATH, f"voice_{int(time.time())}.mp3")
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# Main loop
if __name__ == "__main__":
    print("Robot Assistant ready. Say something or say 'exit' to quit.")

    while True:
        user_text = get_voice_input()

        if not user_text.strip():
            print("Didn't catch that. Try again.")
            continue

        if "exit" in user_text.lower():
            speak("Goodbye friend")
            break

        response = get_gemini_response(user_text)
        print("Robot says:", response)
        speak(response)
