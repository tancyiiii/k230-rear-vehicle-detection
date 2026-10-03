from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ONNX models on the local validation split.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--data", default="../config/data_local.yaml")
    parser.add_argument("--imgsz", nargs="+", type=int, required=True)
    parser.add_argument("--output-dir", default="../reports")
    parser.add_argument("--batch", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.models) != len(args.imgsz):
        raise SystemExit("--models and --imgsz must have the same length")
    base = Path(__file__).resolve().parent
    data = (base / args.data).resolve()
    out_dir = (base / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "onnx_validation.json"
    summaries = {}
    if summary_path.is_file():
        try:
            summaries = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summaries = {}

    for model_path, size in zip(args.models, args.imgsz, strict=True):
        model_file = (base / model_path).resolve()
        print(f"\n=== validating {model_file.name} at {size} ===", flush=True)
        model = YOLO(str(model_file), task="detect")
        results = model.val(
            data=str(data),
            imgsz=size,
            batch=args.batch,
            device="cpu",
            workers=0,
            plots=False,
            save_json=False,
            verbose=True,
        )
        key = f"{model_file.stem}_{size}"
        record = {
            "model": str(model_file),
            "imgsz": size,
            "metrics": {k: float(v) for k, v in results.results_dict.items()},
            "speed_ms_per_image": {k: float(v) for k, v in results.speed.items()},
            "class_names": {int(k): v for k, v in results.names.items()},
        }
        summaries[key] = record
        print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)

    output = out_dir / "onnx_validation.json"
    output.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved: {output}")


if __name__ == "__main__":
    main()

