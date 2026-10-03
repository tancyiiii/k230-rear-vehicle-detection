from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "        capture_ms = 0\n        pre_ms = 0\n        kpu_ms = 0\n        post_ms = 0\n        risk_ms = 0\n",
    "        capture_ms = 0\n        detect_ms = 0\n        risk_ms = 0\n",
    1,
)
text = text.replace(
    "                vehicle_tensors = vehicle_detector.preprocess(frame)\n                vehicle_results = vehicle_detector.inference(vehicle_tensors)\n                vehicle_detections = vehicle_detector.postprocess(vehicle_results)\n                pre_end = time.ticks_ms()\n                person_tensors = person_detector.preprocess(frame)\n                person_results = person_detector.inference(person_tensors)\n                person_detections = person_detector.postprocess(person_results)\n                detections = vehicle_detections + person_detections\n                kpu_end = time.ticks_ms()\n                infer_end = kpu_end\n",
    "                vehicle_tensors = vehicle_detector.preprocess(frame)\n                vehicle_results = vehicle_detector.inference(vehicle_tensors)\n                vehicle_detections = vehicle_detector.postprocess(vehicle_results)\n                person_tensors = person_detector.preprocess(frame)\n                person_results = person_detector.inference(person_tensors)\n                person_detections = person_detector.postprocess(person_results)\n                detections = vehicle_detections + person_detections\n                infer_end = time.ticks_ms()\n",
    1,
)
text = text.replace(
    "                capture_ms += time.ticks_diff(capture_end, loop_start)\n                pre_ms += time.ticks_diff(pre_end, capture_end)\n                kpu_ms += time.ticks_diff(kpu_end, pre_end)\n                post_ms += time.ticks_diff(infer_end, kpu_end)\n                risk_ms += time.ticks_diff(track_end, infer_end)\n",
    "                capture_ms += time.ticks_diff(capture_end, loop_start)\n                detect_ms += time.ticks_diff(infer_end, capture_end)\n                risk_ms += time.ticks_diff(track_end, infer_end)\n",
    1,
)
text = text.replace(
    'print("STATS FPS={:.2f} DET={} RISK={} ms(cap={:.1f},pre={:.1f},kpu={:.1f},post={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,\n                            len(draw_detections),\n                            overall_risk,\n                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            pre_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            kpu_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            post_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            risk_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            draw_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            show_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                        ))',
    'print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,\n                            len(draw_detections),\n                            len(vehicle_detections),\n                            len(person_detections),\n                            overall_risk,\n                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            detect_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            risk_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            draw_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                            show_ms / float(DEBUG_LOG_EVERY_FRAMES),\n                        ))',
    1,
)
text = text.replace(
    "                    capture_ms = 0\n                    pre_ms = 0\n                    kpu_ms = 0\n                    post_ms = 0\n                    risk_ms = 0\n",
    "                    capture_ms = 0\n                    detect_ms = 0\n                    risk_ms = 0\n",
    1,
)
path.write_text(text, encoding="utf-8")
print("patched", path)
