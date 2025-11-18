from ultralytics import YOLO
from pathlib import Path
import torch
from src.config import load_config


class YOLOv11Inference:
    def __init__(self, model_name):
        # Auto-select CPU or GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Using device: {self.device}")

        # Load YOLO model
        self.model = YOLO(model_name)
        self.model.to(self.device)

        # Load configuration
        config = load_config()
        self.conf_threshold = config["model"]["conf_threshold"]
        self.extensions = config["data"]["image_extension"]


    def process_image(self, image_path):
        """Run inference on a single image and extract detections."""

        # YOLO prediction
        results = self.model.predict(
            source=image_path,
            conf=self.conf_threshold,
            device=self.device
        )

        detections = []
        class_counts = {}

        for result in results:
            for box in result.boxes:
                cls = result.names[int(box.cls)]
                conf = float(box.conf)
                bbox = box.xyxy[0].tolist()

                detections.append({
                    "class": cls,
                    "confidence": conf,
                    "bbox": bbox,
                    "count": 1
                })

                class_counts[cls] = class_counts.get(cls, 0) + 1

        # Update count for each detection
        for det in detections:
            det["count"] = class_counts[det["class"]]

        return {
            "image_path": str(image_path),
            "detections": detections,
            "total_objects": len(detections),
            "unique_class": list(class_counts.keys()),
            "class_counts": class_counts
        }


    def process_directory(self, directory):
        """Run inference on all images inside a directory."""
        metadata = []
        patterns = [f"*{ext}" for ext in self.extensions]

        image_paths = []
        for pattern in patterns:
            image_paths.extend(Path(directory).glob(pattern))

        for img_path in image_paths:
            try:
                result = self.process_image(img_path)
                metadata.append(result)
            except Exception as e:
                print(f"[ERROR] Failed processing {img_path}: {e}")
                continue

        return metadata
