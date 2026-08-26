import base64
import os
import subprocess
import threading
import time
import cv2
import requests

GEMINI_API_KEY = "AQ.Ab8RN6LgXKH0HzgemRnozckOXrOHHob3lfaQtX7NqyB4Mm5Pfg"


def speak_blocking(text):
  try:
    safe_text = text.replace('"', "'")
    powershell_cmd = (
        "Add-Type -AssemblyName System.Speech; (New-Object"
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
  print("☁️ Sending frame to Gemini Cloud API...")
  success, encoded_image = cv2.imencode(".jpg", frame)
  if not success:
    return "Failed to encode image for Gemini."

  image_bytes = encoded_image.tobytes()
  encoded_base64 = base64.b64encode(image_bytes).decode("utf-8")
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

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

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=25)
    if response.status_code == 200:
      data = response.json()
      candidate = data.get("candidates", [])[0]
      return (
          candidate.get("content", {})
          .get("parts", [])[0]
          .get("text", "")
          .strip()
      )
  except Exception as e:
    print(f"Gemini error: {e}")
  return "Cloud AI connection failed."


server_url = "http://127.0.0.1:8000"
cap = cv2.VideoCapture(0)

print("\n🚀 SEER Smart Glasses Console Client (Dual-Model Local Mode Active)!")
print("  [1] Detect Objects Locally (YOLOv8n)")
print("  [2] Translate Sign Language Locally (Custom ArSL best.pt)")
print("  [3] Read Text / OCR Locally")
print("  [4] Gemini Cloud Fallback (Multimodal Backup)")
print("  [q] Quit\n")

speak_async("Seer dual model local system online.")

while cap.isOpened():
  choice = input(
      "Enter command [1=Objects, 2=Sign Language, 3=OCR, 4=Gemini Backup,"
      " q=Quit]: "
  ).strip()

  if choice.lower() == "q":
    break

  ret, frame = cap.read()
  if not ret:
    print("Failed to grab camera frame.")
    continue

  success, encoded_image = cv2.imencode(".jpg", frame)

  # Mode 1: Local Objects
  if choice == "1":
    print("\n💡 Local Object Detection Triggered!")
    play_chime(800, 1200)
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
          current_objects = [item["object"] for item in data.get("objects_detected", [])]
          if current_objects:
            obj_str = ", ".join(set(current_objects))
            print(f"🔊 AI Response: I see {obj_str}")
            speak_blocking(f"I see {obj_str}")
          else:
            speak_blocking("I don't see any recognized objects.")
      except Exception as e:
        print(f"Connection error: {e}")

  # Mode 2: Local Sign Language using your new best.pt model
  elif choice == "2":
    print("\n👐 Local Sign Language Translation Triggered!")
    play_chime(1200, 1600)
    if success:
      try:
        response = requests.post(
            f"{server_url}/process-signs",
            files={
                "file": ("frame.jpg", encoded_image.tobytes(), "image/jpeg")
            },
            timeout=5,
        )
        if response.status_code == 200:
          data = response.json()
          signs = data.get("signs_detected", [])
          current_signs = [item["sign"] for item in signs]
          if current_signs:
            sign_str = ", ".join(set(current_signs))
            print(f"🔊 Sign Translated: {sign_str}")
            speak_blocking(sign_str)
          else:
            speak_blocking("No sign language gesture recognized.")
      except Exception as e:
        print(f"Connection error: {e}")

  # Mode 3: Local OCR Text Reading
  elif choice == "3":
    print("\n📄 Local OCR Text Reading Triggered!")
    play_chime(1000, 1500)
    if success:
      try:
        response = requests.post(
            f"{server_url}/process-ocr",
            files={
                "file": ("frame.jpg", encoded_image.tobytes(), "image/jpeg")
            },
            timeout=10,
        )
        if response.status_code == 200:
          text_read = response.json().get("text_read", "")
          print(f"🔊 OCR Read: {text_read}")
          speak_blocking(text_read)
      except Exception as e:
        print(f"Connection error: {e}")

  # Mode 4: Gemini Cloud Backup (saves your credits)
  elif choice == "4":
    print("\n☁️ Gemini Cloud Backup Triggered!")
    play_chime(900, 1300)
    speak_blocking("Connecting to cloud AI.")
    prompt = "Look at this image and describe what the user needs to know concisely."
    result_text = analyze_with_gemini(frame, prompt)
    print(f"🔊 Gemini Response: {result_text}")
    speak_blocking(result_text)

  else:
    print("Invalid choice.")

cap.release()
print("SEER Client shut down safely.")