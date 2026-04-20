from flask import Flask, render_template, request, flash, redirect, url_for
import os
import pathlib
import cv2
from ultralytics import YOLO
from werkzeug.utils import secure_filename

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "mask_detection_secret_key"  # required for flash messages

# ── Absolute base directory (works no matter where the app is launched from) ─
BASE_DIR = pathlib.Path(__file__).parent

# ── Load YOLO model using an absolute path ───────────────────────────────────
MODEL_PATH = BASE_DIR / "model" / "best.pt"
model = YOLO(str(MODEL_PATH))

# ── Upload / output folders ──────────────────────────────────────────────────
UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
OUTPUT_FOLDER = str(BASE_DIR / "static" / "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Allowed image extensions ─────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}

def allowed_file(filename: str) -> bool:
    """Return True only if the filename has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/detect_image", methods=["POST"])
def detect_image():
    # 1. Check that a file key exists in the request
    if "image" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["image"]

    # 2. Check that the user actually selected a file
    if file.filename == "":
        flash("No file selected. Please choose an image.")
        return redirect(url_for("index"))

    # 3. Validate file extension
    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload a JPG, PNG, GIF, BMP, or WEBP image.")
        return redirect(url_for("index"))

    # 4. Sanitise the filename to prevent path-traversal attacks
    filename = secure_filename(file.filename)

    # 5. Save the uploaded file
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # 6. Run YOLO inference with error handling
    try:
        results = model(filepath)
    except Exception as e:
        flash(f"Model inference failed: {e}")
        return redirect(url_for("index"))

    # 7. Write the annotated output image
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    try:
        for r in results:
            img = r.plot()
            cv2.imwrite(output_path, img)
    except Exception as e:
        flash(f"Failed to save output image: {e}")
        return redirect(url_for("index"))

    # 8. Pass only the path *relative to the static folder* to the template
    #    so Jinja2 / url_for('static', ...) works correctly.
    relative_output = "outputs/" + filename

    return render_template("index.html", image=relative_output)


if __name__ == "__main__":
    app.run(debug=True)
