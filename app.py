from flask import Flask, render_template, Response
import cv2
import pathlib
from ultralytics import YOLO

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Absolute paths ─────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).parent
MODEL_PATH = BASE_DIR / "model" / "best.pt"

# ── Load YOLO model ────────────────────────────────────────────────────────────
model = YOLO(str(MODEL_PATH))

# ── Frame generator ────────────────────────────────────────────────────────────
def generate_frames():
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Run YOLO detection
            results = model(frame, conf=0.5, verbose=False)

            # Draw bounding boxes on frame
            for r in results:
                frame = r.plot()

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            # Yield as multipart stream
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        cap.release()

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)
