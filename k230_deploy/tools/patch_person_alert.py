from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    'VEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5, 0.5]',
    'VEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5, 0.8]',
    1,
)
text = text.replace(
    'SAFE_DISTANCE_M = 25.0\nDANGER_DISTANCE_M = 10.0\nATTENTION_SPEED_MPS = 0.2\n',
    'SAFE_DISTANCE_M = 25.0\nDANGER_DISTANCE_M = 10.0\nATTENTION_SPEED_MPS = 0.2\nPERSON_SAFE_DISTANCE_M = 30.0\nPERSON_DANGER_DISTANCE_M = 12.0\n',
    1,
)
old_risk = '''            if distance <= DANGER_DISTANCE_M:
                risk = 2
            elif distance <= SAFE_DISTANCE_M and (
                previous_distance is None or speed >= ATTENTION_SPEED_MPS
            ):
                risk = 1
            else:
                risk = 0
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
'''
if old_risk not in text:
    raise SystemExit("risk block not found")
text = text.replace(old_risk, new_risk, 1)
text = text.replace(
    '        frequency = 1800 if level == 1 else 2600\n        interval_ms = 1200 if level == 1 else 450\n        duration_s = 0.08 if level == 1 else 0.12\n',
    '        frequency = 1000\n        interval_ms = 900 if level == 1 else 350\n        duration_s = 0.25 if level == 1 else 0.35\n',
    1,
)
path.write_text(text, encoding="utf-8")
print("patched", path)
