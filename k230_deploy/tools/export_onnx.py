from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the rear-vehicle YOLO11 model to fixed-shape ONNX.")
    parser.add_argument("--weights", default="../models/best.pt")
    parser.add_argument("--output-dir", default="../onnx")
    parser.add_argument("--sizes", nargs="+", type=int, default=[320, 640])
    parser.add_argument("--opset", type=int, default=13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = Path(__file__).resolve().parent
    weights = (base / args.weights).resolve()
    output_dir = (base / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not weights.is_file():
        raise SystemExit(f"model not found: {weights}")

    for size in args.sizes:
        print(f"\n=== exporting ONNX {size}x{size} ===", flush=True)
        model = YOLO(str(weights))
        exported = Path(
            model.export(
                format="onnx",
                imgsz=size,
                batch=1,
                dynamic=False,
                simplify=True,
                opset=args.opset,
                half=False,
                nms=False,
                device="cpu",
                verbose=True,
            )
        ).resolve()
        target = output_dir / f"best_{size}.onnx"
        if exported != target:
            shutil.copy2(exported, target)
        print(f"saved: {target}\n", flush=True)


if __name__ == "__main__":
    main()
