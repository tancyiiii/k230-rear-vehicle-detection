from __future__ import annotations

import argparse
import os
from pathlib import Path

import cv2
import nncase
import numpy as np


def letterbox(image: np.ndarray, size: int, color: int = 114) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(size / width, size / height)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), color, dtype=np.uint8)
    left = (size - new_width) // 2
    top = (size - new_height) // 2
    canvas[top:top + new_height, left:left + new_width] = resized
    return canvas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--calibration-dir", required=True)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--input-size", type=int, default=320)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    onnx_path = Path(os.path.abspath(args.onnx))
    output_path = Path(os.path.abspath(args.output))
    calib_dir = Path(os.path.abspath(args.calibration_dir))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        p for p in calib_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
    )
    if len(image_paths) > args.samples:
        indices = np.linspace(0, len(image_paths) - 1, args.samples).round().astype(int)
        image_paths = [image_paths[i] for i in indices]
    if not image_paths:
        raise SystemExit(f"no calibration images found in {calib_dir}")

    tensors = []
    for path in image_paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            continue
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (args.input_size, args.input_size), interpolation=cv2.INTER_LINEAR)
        tensor = image.transpose(2, 0, 1)[None, ...].astype(np.uint8)
        tensors.append(tensor)
    if not tensors:
        raise SystemExit("failed to load calibration images")

    options = nncase.CompileOptions()
    options.target = "k230"
    options.preprocess = True
    options.swapRB = False
    options.input_type = "uint8"
    options.input_shape = [1, 3, args.input_size, args.input_size]
    options.input_range = [0, 1]
    options.mean = [0, 0, 0]
    options.std = [1, 1, 1]
    options.input_layout = "NCHW"
    options.output_layout = "NCHW"
    options.letterbox_value = 114
    options.dump_asm = False
    options.dump_ir = False

    compiler = nncase.Compiler(options)
    compiler.import_onnx(onnx_path.read_bytes(), nncase.ImportOptions())

    ptq = nncase.PTQTensorOptions()
    ptq.samples_count = len(tensors)
    ptq.quant_type = "uint8"
    ptq.w_quant_type = "uint8"
    ptq.calibrate_method = "Kld"
    ptq.finetune_weights_method = "NoFineTuneWeights"
    ptq.set_tensor_data([np.stack(tensors, axis=0)])

    print(f"compiling {onnx_path.name} with {len(tensors)} calibration images...", flush=True)
    compiler.use_ptq(ptq)
    compiler.compile()
    kmodel = compiler.gencode_tobytes()
    output_path.write_bytes(kmodel)
    print(f"saved {output_path} ({len(kmodel)} bytes)")


if __name__ == "__main__":
    main()






