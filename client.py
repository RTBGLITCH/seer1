import base64
import os
import subprocess
import threading
import time
import cv2
import requests

# Your Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6LgXKH0HzgemRnozckOXrOHHob3lfaQtX7NqyB4Mm5Pfg"


def speak_blocking(text):
  """Synchronous speech helper to prevent voice overlapping."""
  try:
    safe_text = text.replace('"', "'")
    powershell_cmd = (
        f"Add-Type -AssemblyName System.Speech; (New-Object"
        f" System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe_text}')"
    )
    subprocess.run(
        ["powershell", "-Command", powershell_cmd],
        capture_output=True,
        text=True,
    )
  except Exception as e:
    print(f"Speech error: {e}")


def speak_async(text):
  """Run speech in a background thread."""
  t = threading.Thread(target=speak_blocking, args=(text,))
  t.daemon = True
  t.start()


def play_chime(freq1, freq2):
  try:
    import winsound

    winsound.Beep(freq1, 150)
    winsound.Beep(freq2, 200)
  except:
    pass


def analyze_with_gemini(frame, prompt_text):
  """Sends the live camera frame directly to Google Gemini API with expanded timeout and retries."""
  print("☁️ Sending frame to Gemini Cloud API...")
  success, encoded_image = cv2.imencode(".jpg", frame)
  if not success:
    return "Failed to encode image for Gemini."

  image_bytes = encoded_image.tobytes()
  encoded_base64 = base64.b64encode(image_bytes).decode("utf-8")

  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"

  headers = {"Content-Type": "application/json"}
  payload = {
      "contents": [{
          "parts": [
              {"text": prompt_text},
              {
                  "inline_data": {
                      "mime_type": "image/jpeg",
                      "data": encoded_base64,
                  }
              },
          ]
      }]
  }

  # Try up to 2 times with a 25-second timeout
  for attempt in range(2):
    try:
      response = requests.post(url, json=payload, headers=headers, timeout=25)
      if response.status_code == 200:
        data = response.json()
        candidate = data.get("candidates", [])[0]
        text_response = (
            candidate.get("content", {}).get("parts", [])[0].get("text", "")
        )
        return text_response.strip()
      else:
        print(f"Gemini API Error: {response.text}")
        return "Cloud AI analysis failed."
    except requests.exceptions.Timeout:
      print(f"⚠️ Request timed out (Attempt {attempt+1}/2). Retrying...")
      time.sleep(1)
    except Exception as e:
      print(f"Gemini Request Exception: {e}")
      return "Connection error with Gemini API."

  return "Cloud AI connection timed out."


server_url = "http://127.0.0.1:8000"
cap = cv2.VideoCapture(0)

print("\n🚀 SEER Smart Glasses Console Client Active (Hybrid Mode)!")
print("Select Backend Engine:")
print("  [L] Local Server Backend (FastAPI + YOLO + EasyOCR)")
print("  [G] Gemini Cloud API (Google Cloud Multimodal Vision)")
mode_choice = input("Choose engine [L or G]: ").strip().lower()

engine_mode = "gemini" if mode_choice == "g" else "local"
engine_name = (
    "Gemini Cloud API" if engine_mode == "gemini" else "Local FastAPI Server"
)
print(f"\n✅ Active Engine: {engine_name}\n")

print("Modes during run:")
print("  [1] Detect Objects (What's this?)")
print("  [2] Read Text / Signs (Read text)")
print("  [3] Translate Sign Language (Hand Gestures)")
print("  [q] Quit\n")

speak_async(f"Seer system online using {engine_name} backend.")

while cap.isOpened():
  choice = input(
      "Enter command [1 = Objects, 2 = OCR, 3 = Sign Language, q = Quit]: "
  ).strip()

  if choice.lower() == "q":
    break

  ret, frame = cap.read()
  if not ret:
    print("Failed to grab camera frame.")
    continue

  if choice == "1":
    print("\n💡 Object Detection Triggered!")
    play_chime(800, 1200)

    if engine_mode == "gemini":
      speak_blocking("Analyzing surroundings with Gemini.")
      prompt = (
          "You are SEER, an assistive AI for smart glasses. Look at this image"
          " and briefly describe what objects are present in 1-2 concise"
          " sentences."
      )
      result_text = analyze_with_gemini(frame, prompt)
      print(f"🔊 Gemini Response: {result_text}")
      speak_blocking(result_text)
    else:
      speak_blocking("Analyzing surroundings locally.")
      success, encoded_image = cv2.imencode(".jpg", frame)
      if success:
        try:
          response = requests.post(
              f"{server_url}/process-frame",
              files={
                  "file": ("frame.jpg", encoded_image.tobytes(), "image/jpeg")
              },
              timeout=5,
          )
          if response.status_code == 200:
            data = response.json()
            detected = data.get("objects_detected", [])
            current_objects = [item["object"] for item in detected]

            if current_objects:
              object_list_str = ", ".join(set(current_objects))
              print(f"🔊 Local AI Response: I see {object_list_str}")
              speak_blocking(f"I see {object_list_str}")
            else:
              speak_blocking("I don't see any recognized objects right now.")
        except Exception as e:
          print(f"Connection error: {e}")

  elif choice == "2":
    print("\n📄 OCR / Sign Reading Triggered!")
    play_chime(1000, 1500)

    if engine_mode == "gemini":
      speak_blocking("Reading text with Gemini.")
      prompt = (
          "You are SEER, an assistive AI for smart glasses. Look at this image"
          " and read any visible text, signs, or labels clearly and"
          " concisely."
      )
      result_text = analyze_with_gemini(frame, prompt)
      print(f"🔊 Gemini OCR Response: {result_text}")
      speak_blocking(result_text)
    else:
      speak_blocking("Reading text locally.")
      success, encoded_image = cv2.imencode(".jpg", frame)
      if success:
        try:
          response = requests.post(
              f"{server_url}/process-ocr",
              files={
                  "file": ("frame.jpg", encoded_image.tobytes(), "image/jpeg")
              },
              timeout=15,
          )
          if response.status_code == 200:
            data = response.json()
            text_read = data.get("text_read", "I can't see any text.")
            print(f"🔊 Local OCR Read Aloud: {text_read}")
            speak_blocking(text_read)
        except Exception as e:
          print(f"Connection error: {e}")

  elif choice == "3":
    print("\n👐 Sign Language Translation Triggered!")
    play_chime(1200, 1600)
    speak_blocking("Show sign language gesture.")

    time.sleep(1.0)
    ret, sign_frame = cap.read()

    if ret:
      prompt = (
          "You are SEER, a sign language translation assistant for smart"
          " glasses. Look at the hand gesture in this image. Identify what"
          " sign language letter, word, or common expression (like Hello,"
          " Thank you, Stop, Yes, or No) is being shown. Reply with *only* the"
          " translated word or letter concisely."
      )
      result_text = analyze_with_gemini(sign_frame, prompt)
      print(f"🔊 Translated Sign: {result_text}")
      speak_blocking(result_text)
    else:
      speak_blocking("Failed to capture hand gesture.")

  else:
    print("Invalid choice. Please enter 1, 2, 3, or q.")

cap.release()
print("SEER Client shut down safely.")