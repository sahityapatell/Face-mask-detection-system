from flask import Flask, render_template, Response, request, flash, redirect, url_for
import os
import pathlib
import cv2
from ultralytics import YOLO
from werkzeug.utils import secure_filename

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "mask_detection_secret_key"

# ── Absolute paths ─────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).parent
MODEL_PATH = BASE_DIR / "model" / "best.pt"

# ── Load YOLO model ────────────────────────────────────────────────────────────
model = YOLO(str(MODEL_PATH))

# ── Upload / output folders ────────────────────────────────────────────────────
UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
OUTPUT_FOLDER = str(BASE_DIR / "static" / "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Allowed extensions ─────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Live stream generator ──────────────────────────────────────────────────────
def generate_frames():
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            results = model(frame, conf=0.5, verbose=False)
            for r in results:
                frame = r.plot()

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

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

@app.route('/detect_image', methods=['POST'])
def detect_image():
    if 'image' not in request.files:
        flash('No file part in the request.')
        return redirect(url_for('index'))

    file = request.files['image']

    if file.filename == '':
        flash('No file selected. Please choose an image.')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a JPG, PNG, GIF, BMP, or WEBP image.')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        results = model(filepath)
    except Exception as e:
        flash(f'Model inference failed: {e}')
        return redirect(url_for('index'))

    output_path = os.path.join(OUTPUT_FOLDER, filename)
    try:
        for r in results:
            img = r.plot()
            cv2.imwrite(output_path, img)
    except Exception as e:
        flash(f'Failed to save output image: {e}')
        return redirect(url_for('index'))

    relative_output = 'outputs/' + filename
    return render_template('index.html', image=relative_output)

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)
