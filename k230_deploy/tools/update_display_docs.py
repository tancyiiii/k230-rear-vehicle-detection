from pathlib import Path
readme=Path(r"C:\k230_deploy\README.md")
text=readme.read_text(encoding="utf-8")
text=text.replace("主程序默认使用板载 ST7701 屏幕：", "主程序默认使用 CanMV IDE 虚拟帧缓冲：")
text=text.replace("DISPLAY_MODE = \"lcd\"", "DISPLAY_MODE = \"virt\"", 1)
text=text.replace("使用 CanMV IDE 虚拟显示时改成：", "使用板载 ST7701 LCD 时改成：")
text=text.replace("DISPLAY_MODE = \"virt\"\n```\n\n使用 HDMI 时改成：", "DISPLAY_MODE = \"lcd\"\n```\n\n使用 HDMI 时改成：", 1)
if "## 14. CanMV IDE 实时画面显示" not in text:
    text += """
## 14. CanMV IDE 实时画面显示

最终版本使用：

```python
DISPLAY_MODE = "virt"
```

在 CanMV IDE 中打开并运行 `rear_vehicle_yolo11.py`，右侧帧缓冲会显示：

- 摄像头实时画面
- 车辆和人物检测框
- 类别、置信度和估算距离
- 当前风险状态

IDE 实测帧缓冲分辨率为 `800×480`，显示刷新约 `28.6 FPS`。
"""
readme.write_text(text, encoding="utf-8")

bp=Path(r"C:\k230_deploy\reports\board_test.md")
bt=bp.read_text(encoding="utf-8")
if "## CanMV IDE 实时画面" not in bt:
    bt += """
## CanMV IDE 实时画面

- 已使用 `DISPLAY_MODE="virt"` 在 CanMV IDE 中运行成功。
- IDE 帧缓冲分辨率 `800×480`。
- IDE 显示刷新约 `28.6 FPS`。
- 画面包含摄像头图像、检测框、类别、距离和风险状态。
"""
bp.write_text(bt, encoding="utf-8")

sp=Path(r"C:\k230_deploy\reports\solution_status.md")
st=sp.read_text(encoding="utf-8")
st=st.replace("| 板载 LCD 实时显示 | 完成 | ST7701 800x480，自动启动画面正常 |", "| CanMV IDE 实时显示 | 完成 | 800x480 帧缓冲，约 28.6 FPS 显示 |")
sp.write_text(st, encoding="utf-8")
print("docs updated")
