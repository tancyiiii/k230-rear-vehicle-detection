from pathlib import Path
readme=Path(r"C:\k230_deploy\README.md")
t=readme.read_text(encoding="utf-8")
if "黑屏问题已修复" not in t:
    t += """
## 15. IDE 黑屏问题修复

虚拟显示改为官方双层显示方式：

- YUV 视频层：显示摄像头实时画面。
- ARGB OSD 层：叠加检测框、类别、距离和风险状态。

IDE 实测帧缓冲分辨率 `800×480`，RGB 直方图均值约为 `109/108/106`，显示刷新约 `28.6 FPS`。
"""
readme.write_text(t, encoding="utf-8")

bp=Path(r"C:\k230_deploy\reports\board_test.md")
b=bp.read_text(encoding="utf-8")
if "IDE 黑屏修复" not in b:
    b += """
## IDE 黑屏修复

原实现直接显示 RGB565 快照，IDE 中为近黑图像。现改为官方双层管线：

- YUV 视频层显示摄像头原图。
- ARGB OSD 层叠加检测结果。

验证结果：

- 分辨率：800×480
- RGB 直方图均值约 109/108/106
- IDE 显示刷新约 28.6 FPS
"""
bp.write_text(b, encoding="utf-8")
print("docs updated")
