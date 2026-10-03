from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
t=t.replace('DISPLAY_MODE = "lcd"  # "lcd" physical screen, "virt" for CanMV IDE, "hdmi"','DISPLAY_MODE = "virt"  # "virt" for CanMV IDE, "lcd" physical screen, "hdmi"')
p.write_text(t,encoding="utf-8")
print("patched",p)
