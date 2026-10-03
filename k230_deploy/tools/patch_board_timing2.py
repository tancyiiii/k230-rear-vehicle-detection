from pathlib import Path

base = Path(r"C:\k230_deploy\board")
replacements = {
    "        infer_ms = 0\n        other_ms = 0\n": "        pre_ms = 0\n        kpu_ms = 0\n        post_ms = 0\n        risk_ms = 0\n",
    "                detections = detector.run(frame)\n                infer_end = time.ticks_ms()\n": "                tensors = detector.preprocess(frame)\n                pre_end = time.ticks_ms()\n                results = detector.inference(tensors)\n                kpu_end = time.ticks_ms()\n                detections = detector.postprocess(results)\n                infer_end = time.ticks_ms()\n",
    "                capture_ms += time.ticks_diff(capture_end, loop_start)\n                infer_ms += time.ticks_diff(infer_end, capture_end)\n                other_ms += time.ticks_diff(track_end, infer_end)\n": "                capture_ms += time.ticks_diff(capture_end, loop_start)\n                pre_ms += time.ticks_diff(pre_end, capture_end)\n                kpu_ms += time.ticks_diff(kpu_end, pre_end)\n                post_ms += time.ticks_diff(infer_end, kpu_end)\n                risk_ms += time.ticks_diff(track_end, infer_end)\n",
    'print("STATS FPS={:.2f} DET={} RISK={} ms(cap={:.1f},inf={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n': 'print("STATS FPS={:.2f} DET={} RISK={} ms(cap={:.1f},pre={:.1f},kpu={:.1f},post={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n',
    "                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            infer_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            other_ms / float(DEBUG_LOG_EVERY_FRAMES),\n": "                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            pre_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            kpu_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            post_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            risk_ms / float(DEBUG_LOG_EVERY_FRAMES),\n",
    "                    infer_ms = 0\n                    other_ms = 0\n": "                    pre_ms = 0\n                    kpu_ms = 0\n                    post_ms = 0\n                    risk_ms = 0\n",
}
for name in ("rear_vehicle_yolo11.py", "rear_vehicle_yolo11_640.py"):
    path = base / name
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f"missing in {path}: {old!r}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("patched", path)
