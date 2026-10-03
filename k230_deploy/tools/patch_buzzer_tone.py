from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
text = text.replace("BUZZER_VOLUME = 100\n", "BUZZER_DUTY = 50\n", 1)
text = text.replace(
    "        frequency = 1000\n        interval_ms = 900 if level == 1 else 350\n        duration_ms = 250 if level == 1 else 350\n",
    "        frequency = 2700\n        interval_ms = 700 if level == 1 else 220\n        duration_ms = 180 if level == 1 else 240\n",
    1,
)
text = text.replace(
    "self.buzzer.on(frequency, BUZZER_VOLUME, 0)",
    "self.buzzer.on(frequency, BUZZER_DUTY, 0)",
    1,
)
path.write_text(text, encoding="utf-8")
print("patched", path)
