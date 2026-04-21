from ultralytics import YOLO
import pathlib

def main():
    BASE_DIR = pathlib.Path(__file__).parent

    model = YOLO("yolov8s.pt")

    model.train(
        data=str(BASE_DIR / "data.yaml"),
        epochs=20,
        imgsz=640,
        device=0,
        batch=16,
        workers=0
    )

if __name__ == "__main__":
    main()