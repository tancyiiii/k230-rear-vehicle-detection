from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")
old = '''        self.level = 0
        self.last_beep_ms = 0

    def update(self, level):
        if self.buzzer is None:
            return
        now_ms = time.ticks_ms()
        if level == 0:
            if self.level != 0:
                self.buzzer.off()
            self.level = 0
            return

        frequency = 1000
        interval_ms = 900 if level == 1 else 350
        duration_s = 0.25 if level == 1 else 0.35
        if self.level != level:
            self.last_beep_ms = 0
        if self.last_beep_ms == 0 or time.ticks_diff(now_ms, self.last_beep_ms) >= interval_ms:
            self.buzzer.on(frequency, BUZZER_VOLUME, duration_s)
            self.last_beep_ms = now_ms
        self.level = level
'''
new = '''        self.level = 0
        self.last_beep_ms = 0
        self.beep_until_ms = 0
        self.beep_active = False

    def update(self, level):
        if self.buzzer is None:
            return
        now_ms = time.ticks_ms()
        if level == 0:
            if self.beep_active or self.level != 0:
                self.buzzer.off()
            self.beep_active = False
            self.level = 0
            return

        frequency = 1000
        interval_ms = 900 if level == 1 else 350
        duration_ms = 250 if level == 1 else 350

        if self.level != level:
            if self.beep_active:
                self.buzzer.off()
                self.beep_active = False
            self.last_beep_ms = 0

        if self.beep_active and time.ticks_diff(now_ms, self.beep_until_ms) >= 0:
            self.buzzer.off()
            self.beep_active = False

        if not self.beep_active and (
            self.last_beep_ms == 0 or time.ticks_diff(now_ms, self.last_beep_ms) >= interval_ms
        ):
            self.buzzer.on(frequency, BUZZER_VOLUME, 0)
            self.beep_active = True
            self.beep_until_ms = now_ms + duration_ms
            self.last_beep_ms = now_ms
        self.level = level
'''
if old not in text:
    raise SystemExit("alert block not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("patched", path)
