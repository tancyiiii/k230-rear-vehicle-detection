from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
old="        if output.shape[0] <= 20:\n            output = output.transpose()\n"
new="        if output.shape[0] < output.shape[1]:\n            output = output.transpose()\n"
if old not in t:
    raise SystemExit("orientation block not found")
t=t.replace(old,new,1)
p.write_text(t,encoding="utf-8")
print("patched")
