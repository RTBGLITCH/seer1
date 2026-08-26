import cv2
import easyocr
import numpy as np
from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO

app = FastAPI()

print("Loading AI models...")
# 1. Standard general object detection model
general_model = YOLO("yolov8n.pt")

# 2. Your custom Arabic Sign Language model trained on Colab
sign_model = YOLO("best.pt")

# Initialize EasyOCR reader for text reading
ocr_reader = easyocr.Reader(["en"], gpu=False)
print("All models loaded successfully!")


@app.post("/process-frame")
async def process_frame(file: UploadFile = File(...)):
  contents = await file.read()
  nparr = np.frombuffer(contents, np.uint8)
  frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

  results = general_model(frame, verbose=False)
  detected_objects = []

  for r in results:
    for box in r.boxes:
      cls_id = int(box.cls[0])
      conf = float(box.conf[0])
      class_name = general_model.names[cls_id]
      detected_objects.append(
          {"object": class_name, "confidence": round(conf, 2)}
      )

  return {
      "status": "success",
      "objects_detected": detected_objects,
      "count": len(detected_objects),
  }


@app.post("/process-signs")
async def process_signs(file: UploadFile = File(...)):
  contents = await file.read()
  nparr = np.frombuffer(contents, np.uint8)
  frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

  # Run inference using your custom model with a lower confidence threshold for testing
  results = sign_model(frame, verbose=False, conf=0.10)
  detected_signs = []

  for r in results:
    for box in r.boxes:
      cls_id = int(box.cls[0])
      conf = float(box.conf[0])
      sign_name = sign_model.names[cls_id]
      print(f"👉 [SIGN DEBUG] Detected: {sign_name} ({conf:.2f})")
      detected_signs.append({"sign": sign_name, "confidence": round(conf, 2)})

  return {
      "status": "success",
      "signs_detected": detected_signs,
      "count": len(detected_signs),
  }


@app.post("/process-ocr")
async def process_ocr(file: UploadFile = File(...)):
  contents = await file.read()
  nparr = np.frombuffer(contents, np.uint8)
  frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

  ocr_results = ocr_reader.readtext(frame)
  extracted_texts = []
  for _, text, confidence in ocr_results:
    if confidence > 0.2:
      extracted_texts.append(text.strip())

  if extracted_texts:
    full_text = " ".join(extracted_texts)
    spoken_response = f"Sign reads: {full_text}"
    return {"status": "success", "text_read": spoken_response}
  else:
    return {"status": "success", "text_read": "I can't see any text or signs."}


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="0.0.0.0", port=8000)