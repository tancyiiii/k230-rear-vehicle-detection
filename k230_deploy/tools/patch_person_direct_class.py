from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '        class_map,\n        confidence_threshold=CONFIDENCE_THRESHOLD,\n        debug_mode=0,\n',
    '        class_map,\n        confidence_threshold=CONFIDENCE_THRESHOLD,\n        target_class_index=None,\n        debug_mode=0,\n',
    1,
)
text = text.replace(
    '        self.confidence_threshold = confidence_threshold\n        self.x_factor',
    '        self.confidence_threshold = confidence_threshold\n        self.target_class_index = target_class_index\n        self.x_factor',
    1,
)
text = text.replace(
    '        best_scores = np.max(scores_data, axis=1)\n        best_classes = np.argmax(scores_data, axis=1)\n',
    '        if self.target_class_index is None:\n            best_scores = np.max(scores_data, axis=1)\n            best_classes = np.argmax(scores_data, axis=1)\n        else:\n            index = self.target_class_index\n            best_scores = np.max(scores_data[:, index:index + 1], axis=1)\n            best_classes = None\n',
    1,
)
text = text.replace(
    '            model_class = int(best_classes[index])\n',
    '            if self.target_class_index is None:\n                model_class = int(best_classes[index])\n            else:\n                model_class = self.target_class_index\n',
    1,
)
text = text.replace(
    '            class_map=PERSON_CLASS_MAP,\n            confidence_threshold=0.20,\n            debug_mode=0,\n',
    '            class_map=PERSON_CLASS_MAP,\n            confidence_threshold=0.20,\n            target_class_index=0,\n            debug_mode=0,\n',
    1,
)
text = text.replace(
    '                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:\n                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)\n',
    '                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:\n                    detail_parts = []\n                    for track in current:\n                        detail_parts.append("{}:{:.2f}/{:.1f}m/R{}".format(\n                            LABELS[track["class_id"]],\n                            track["score"],\n                            track["distance_m"],\n                            track["risk"],\n                        ))\n                    detail_text = ";".join(detail_parts)\n                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)\n',
    1,
)
text = text.replace(
    'print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n',
    'print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} DETAILS={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n',
    1,
)
text = text.replace(
    '                            overall_risk,\n                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),',
    '                            overall_risk,\n                            detail_text,\n                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),',
    1,
)
path.write_text(text, encoding="utf-8")
print("patched", path)
