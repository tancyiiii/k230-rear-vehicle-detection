from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
old="        self.osd_img = self.sensor.snapshot(chn=CAM_CHN_ID_0)\n        try:\n            self.osd_img.gamma(2.0)\n"
new="        display_snapshot = self.sensor.snapshot(chn=CAM_CHN_ID_0)\n        self.osd_img = display_snapshot.copy()\n        try:\n            self.osd_img.gamma(2.0)\n"
if old not in t:
    raise SystemExit("display snapshot block not found")
t=t.replace(old,new,1)
p.write_text(t,encoding="utf-8")
print("patched",p)
