from pathlib import Path

for name in ("rear_vehicle_yolo11.py", "rear_vehicle_yolo11_640.py"):
    path = Path(r"C:\k230_deploy\board") / name
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "TRACK_MAX_AGE_MS = 1200",
        "TRACK_MAX_AGE_MS = 1200\nDEBUG_LOG_EVERY_FRAMES = 30",
    )
    text = text.replace(
        "        detector.config_preprocess()\n        tracker = SimpleTracker()",
        "        detector.config_preprocess()\n        print(\"rear vehicle ready:\", KMODEL_PATH, \"display:\", DISPLAY_MODE)\n        tracker = SimpleTracker()",
    )
    text = text.replace(
        "        alert = AlertController()\n\n        while True:",
        "        alert = AlertController()\n        frame_count = 0\n        fps_start_ms = time.ticks_ms()\n\n        while True:",
    )
    text = text.replace(
        "                alert.update(overall_risk)\n                gc.collect()",
        "                alert.update(overall_risk)\n                frame_count += 1\n                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:\n                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)\n                    if elapsed_ms > 0:\n                        print(\"STATS FPS={:.2f} DET={} RISK={}\".format(\n                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,\n                            len(draw_detections),\n                            overall_risk,\n                        ))\n                    fps_start_ms = now_ms\n                gc.collect()",
    )
    path.write_text(text, encoding="utf-8")
    print("patched", path)
