from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    'PERSON_SAFE_DISTANCE_M = 30.0\nPERSON_DANGER_DISTANCE_M = 12.0\n',
    'PERSON_SAFE_DISTANCE_M = 40.0\nPERSON_DANGER_DISTANCE_M = 15.0\nPERSON_HEIGHT_M = 1.7\nRISK_CONFIRM_FRAMES = 2\nSTARTUP_GRACE_MS = 1200\n',
    1,
)
text = text.replace(
    '        class_map,\n        debug_mode=0,\n    ):\n',
    '        class_map,\n        confidence_threshold=CONFIDENCE_THRESHOLD,\n        debug_mode=0,\n    ):\n',
    1,
)
text = text.replace(
    '        self.class_map = class_map\n        self.x_factor',
    '        self.class_map = class_map\n        self.confidence_threshold = confidence_threshold\n        self.x_factor',
    1,
)
text = text.replace(
    'selected = np.nonzero(best_scores >= CONFIDENCE_THRESHOLD)[0]',
    'selected = np.nonzero(best_scores >= self.confidence_threshold)[0]',
    1,
)

old_distance = '''            width_px = max(1.0, float(x2 - x1))
            class_id = _clamp(int(track["class_id"]), 0, len(VEHICLE_WIDTHS_M) - 1)
            distance = self.focal_length_px * VEHICLE_WIDTHS_M[class_id] / width_px
'''
new_distance = '''            width_px = max(1.0, float(x2 - x1))
            height_px = max(1.0, float(y2 - y1))
            class_id = _clamp(int(track["class_id"]), 0, len(VEHICLE_WIDTHS_M) - 1)
            if class_id == PERSON_CLASS_ID:
                distance_by_width = self.focal_length_px * VEHICLE_WIDTHS_M[class_id] / width_px
                distance_by_height = self.focal_length_px * PERSON_HEIGHT_M / height_px
                distance = min(distance_by_width, distance_by_height)
            else:
                distance = self.focal_length_px * VEHICLE_WIDTHS_M[class_id] / width_px
'''
if old_distance not in text:
    raise SystemExit("distance block not found")
text = text.replace(old_distance, new_distance, 1)

old_risk = '''            if class_id == PERSON_CLASS_ID:
                if distance <= PERSON_DANGER_DISTANCE_M:
                    risk = 2
                elif distance <= PERSON_SAFE_DISTANCE_M:
                    risk = 1
                else:
                    risk = 0
            elif distance <= DANGER_DISTANCE_M:
                risk = 2
            elif distance <= SAFE_DISTANCE_M and (
                previous_distance is None or speed >= ATTENTION_SPEED_MPS
            ):
                risk = 1
            else:
                risk = 0
            track["risk"] = risk
            if risk > overall:
                overall = risk
'''
new_risk = '''            if class_id == PERSON_CLASS_ID:
                if distance <= PERSON_DANGER_DISTANCE_M:
                    risk = 2
                elif distance <= PERSON_SAFE_DISTANCE_M:
                    risk = 1
                else:
                    risk = 0
            elif distance <= DANGER_DISTANCE_M:
                risk = 2
            elif distance <= SAFE_DISTANCE_M and (
                previous_distance is None or speed >= ATTENTION_SPEED_MPS
            ):
                risk = 1
            else:
                risk = 0

            if risk == 0:
                track["candidate_risk"] = 0
                track["risk_frames"] = 0
                confirmed_risk = 0
            else:
                if risk == track.get("candidate_risk", 0):
                    track["risk_frames"] = track.get("risk_frames", 0) + 1
                else:
                    track["candidate_risk"] = risk
                    track["risk_frames"] = 1
                confirmed_risk = risk if track["risk_frames"] >= RISK_CONFIRM_FRAMES else 0

            track["risk"] = confirmed_risk
            if confirmed_risk > overall:
                overall = confirmed_risk
'''
if old_risk not in text:
    raise SystemExit("risk block not found")
text = text.replace(old_risk, new_risk, 1)
text = text.replace(
    '                "risk": 0,\n            }',
    '                "candidate_risk": 0,\n                "risk_frames": 0,\n                "risk": 0,\n            }',
    1,
)
text = text.replace(
    '            class_map=PERSON_CLASS_MAP,\n            debug_mode=0,\n        )',
    '            class_map=PERSON_CLASS_MAP,\n            confidence_threshold=0.20,\n            debug_mode=0,\n        )',
    1,
)
text = text.replace(
    '        frame_count = 0\n        fps_start_ms = time.ticks_ms()\n',
    '        startup_ms = time.ticks_ms()\n        frame_count = 0\n        fps_start_ms = startup_ms\n',
    1,
)
text = text.replace(
    '                current, overall_risk = risk_controller.evaluate(tracks, now_ms)\n                track_end = time.ticks_ms()\n',
    '                current, overall_risk = risk_controller.evaluate(tracks, now_ms)\n                if time.ticks_diff(now_ms, startup_ms) < STARTUP_GRACE_MS:\n                    overall_risk = 0\n                track_end = time.ticks_ms()\n',
    1,
)
path.write_text(text, encoding="utf-8")
print("patched", path)
