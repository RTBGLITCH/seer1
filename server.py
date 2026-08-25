import cv2
import easyocr
import numpy as np
from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO

app = FastAPI()

print("Loading AI models...")
model = YOLO("yolov8n.pt")
# Initialize EasyOCR reader for English text
ocr_reader = easyocr.Reader(["en"], gpu=False)
print("Models loaded successfully!")


@app.post("/process-frame")
async def process_frame(file: UploadFile = File(...)):
  contents = await file.read()
  nparr = np.frombuffer(contents, np.uint8)
  frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

  results = model(frame, verbose=False)
  detected_objects = []

  for r in results:
    for box in r.boxes:
      cls_id = int(box.cls[0])
      conf = float(box.conf[0])
      class_name = model.names[cls_id]
      detected_objects.append({"object": class_name, "confidence": round(conf, 2)})

  return {
      "status": "success",
      "objects_detected": detected_objects,
      "count": len(detected_objects),
  }


@app.post("/process-ocr")
async def process_ocr(file: UploadFile = File(...)):
  contents = await file.read()
  nparr = np.frombuffer(contents, np.uint8)
  frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

  # Run EasyOCR on the live frame
  ocr_results = ocr_reader.readtext(frame)

  extracted_texts = []
  for _, text, confidence in ocr_results:
    if confidence > 0.2:
      extracted_texts.append(text.strip())

  if extracted_texts:
    full_text = " ".join(extracted_texts)
    print(f"📄 Sign / Text Detected: {full_text}")

    # Smart sign assistant boost for navigation words
    lower_text = full_text.lower()
    if "exit" in lower_text:
      spoken_response = "Exit sign detected: Proceed towards the exit."
    elif "danger" in lower_text or "caution" in lower_text:
      spoken_response = f"Warning sign detected: {full_text}"
    else:
      spoken_response = f"Sign reads: {full_text}"

    return {"status": "success", "text_read": spoken_response}
  else:
    print("📄 OCR: No signs or text detected.")
    return {"status": "success", "text_read": "I can't see any text or signs."}


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="127.0.0.1", port=8000)