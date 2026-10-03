# K230 实机验证记录

日期：2026-10-02

## 硬件与固件

- 开发板：CanMV K230 YAHBOOM - 1G
- 摄像头：GC2093 CSI2
- CanMV IDE 固件版本：0.4.0
- 串口：COM7
- 显示：CanMV IDE 虚拟显示

## 板上文件

```text
/sdcard/rear_vehicle/labels.txt
/sdcard/rear_vehicle/rear_vehicle_yolo11.py
/sdcard/rear_vehicle/rear_vehicle_yolo11_640.py
/sdcard/rear_vehicle/best_320.kmodel
/sdcard/rear_vehicle/best_640.kmodel
```

## 320 结果

模型成功加载，摄像头和虚拟显示初始化成功，连续运行 12 组统计无异常。

典型输出：

```text
STATS FPS=13.75 DET=1 RISK=2 ms(cap=3.5,pre=1.1,kpu=29.5,post=0.9,risk=0.0,draw=4.7,show=0.7)
STATS FPS=13.68 DET=1 RISK=2 ms(cap=3.4,pre=1.0,kpu=29.7,post=0.7,risk=0.1,draw=0.6,show=0.7)
```

平均表现：

- FPS：约 18~20
- KPU：约 29 ms
- Python 后处理：约 0.9 ms
- 风险等级输出：正常

## 640 结果

模型成功加载，连续运行稳定。

典型输出：

```text
STATS FPS=9.09 DET=0 RISK=0 ms(cap=4.0,pre=3.8,kpu=98.2,post=2.7,risk=0.0,draw=0.5,show=0.6)
```

平均表现：

- FPS：约 9.1
- KPU：约 98 ms
- Python 后处理：约 2.7 ms

## 发现的板端问题与修复

1. `DetectionApp` 的参数名大小写错误，已从 `MODEL_INPUT_SIZE` 修正为 `model_input_size`。
2. 固件 0.4.0 不支持 `sys.print_exception`，已移除该调用。
3. 初版 Python 后处理耗时约 117 ms，改为 `ulab.numpy` 向量化置信度和类别筛选后，降到约 0.9 ms。
4. AI 输入通道改为和模型相同的方形尺寸，减少 AI2D 缩放开销。

## 结论

320 版适合作为当前实时预警默认模型；640 版精度更高但只有约 9 FPS。测距和报警阈值仍需实车标定。

## 开机自动启动验证

已在 `/sdcard/main.py` 写入自动启动入口。软重启后串口自动输出：

```text
MPY: soft reboot
AUTOSTART: rear vehicle recognition
rear vehicle ready: /sdcard/rear_vehicle/best_320.kmodel display: virt
STATS FPS=18.62 DET=1 RISK=2
```

这证明断电极重启后不需要打开 IDE，也不需要手动运行脚本。

## 人物检测验证

新增 `person_320.kmodel`，人物 ONNX 在 COCO128 上 person 类验证：

- mAP50：约 0.531
- mAP50-95：约 0.407
- 板端双模型运行：约 12.8 FPS

运行日志：

```text
STATS FPS=9.84 DET=1 VEH=1 PERSON=0 RISK=2
```

`VEH` 和 `PERSON` 分别统计车辆与人物。当前测试画面没有人物，因此 `PERSON=0`，但人物模型已成功加载并参与每帧推理。

## 蜂鸣器修正验证

- 使用 2700 Hz、duty=50。
- 注意：180 ms 鸣叫，700 ms 周期。
- 危险：240 ms 鸣叫，220 ms 周期。
- 改为非阻塞 PWM 后，自动启动双模型仍约 12.8 FPS。



## 人物解析修正

- 人物模型输出为 84 通道，修正了自动转置条件。
- 直接读取 person 类分数，不参与其他 79 类的 argmax 竞争。
- 人物阈值 0.20，连续 2 帧确认。
- 人物测距同时使用 0.8m 宽度和 1.7m 高度。
- 启动后 1.2 秒内不报警。


## 最终蜂鸣器策略

最终版本已设置：

`python
ENABLE_BUZZER = False
` 

自动启动仍然运行，车辆和人物检测结果继续显示，但蜂鸣器不会发声。已通过重启日志确认 uzzer: False。


## 人物专属蜂鸣验证

实机顺序：

1. 只有车辆：RISK=2、BUZZ=0，不响。
2. 人物进入画面：PERSON=1、BUZZ=2，蜂鸣器触发。
3. 人物离开：PERSON=0、BUZZ=0，恢复静音。


## 板载 LCD 实时显示

- ST7701 LCD 初始化成功。
- 正式识别程序在 LCD 上运行成功。
- 画面包含摄像头实时图像、检测框、类别、距离和风险状态。
- 自动启动后约 13.8 FPS。


## CanMV IDE 实时画面

- 已使用 `DISPLAY_MODE="virt"` 在 CanMV IDE 中运行成功。
- IDE 帧缓冲分辨率 `800×480`。
- IDE 显示刷新约 `28.6 FPS`。
- 画面包含摄像头图像、检测框、类别、距离和风险状态。

## IDE 黑屏修复

原实现直接显示 RGB565 快照，IDE 中为近黑图像。现改为官方双层管线：

- YUV 视频层显示摄像头原图。
- ARGB OSD 层叠加检测结果。

验证结果：

- 分辨率：800×480
- RGB 直方图均值约 109/108/106
- IDE 显示刷新约 28.6 FPS
