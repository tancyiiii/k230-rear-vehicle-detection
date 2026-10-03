from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
t=t.replace("BUZZER_DUTY = 50\n", "ENABLE_BUZZER = False\nBUZZER_DUTY = 50\n", 1)
t=t.replace(
    "        self.buzzer = None\n        if YbBuzzer is not None:\n",
    "        self.buzzer = None\n        if ENABLE_BUZZER and YbBuzzer is not None:\n",
    1,
)
t=t.replace(
    'print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "display:", DISPLAY_MODE)',
    'print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "buzzer:", ENABLE_BUZZER, "display:", DISPLAY_MODE)',
    1,
)
p.write_text(t,encoding="utf-8")
print("patched",p)
