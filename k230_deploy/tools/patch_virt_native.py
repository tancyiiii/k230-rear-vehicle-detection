from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
t=t.replace('DISPLAY_SIZE = [800, 480]','DISPLAY_SIZE = [320, 320]',1)
t=t.replace(
    '        display_frame = ai_frame.to_rgb565()\n        self.osd_img = display_frame.copy(\n            x_scale=float(self.display_size[0]) / float(self.rgb888p_size[0]),\n            y_scale=float(self.display_size[1]) / float(self.rgb888p_size[1]),\n        )\n',
    '        self.osd_img = ai_frame.to_rgb565()\n',
    1,
)
p.write_text(t,encoding="utf-8")
print("patched",p)
