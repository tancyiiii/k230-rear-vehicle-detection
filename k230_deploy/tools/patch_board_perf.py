from pathlib import Path

base = Path(r"C:\k230_deploy\board")
for name, size in (("rear_vehicle_yolo11.py", 320), ("rear_vehicle_yolo11_640.py", 640)):
    path = base / name
    text = path.read_text(encoding="utf-8")
    text = text.replace("RGB888P_SIZE = [640, 480]", f"RGB888P_SIZE = [{size}, {size}]")
    text = text.replace("                gc.collect()", "                if frame_count % 10 == 0:\n                    gc.collect()")
    path.write_text(text, encoding="utf-8")
    print("patched", path)
