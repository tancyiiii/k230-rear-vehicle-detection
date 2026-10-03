# K230 后方来车识别部署包

## 1. 上板验证结果

已在实际开发板上验证：

- 开发板：CanMV K230 YAHBOOM - 1G
- 摄像头：GC2093 CSI2
- CanMV IDE 固件版本：0.4.0
- KMODEL 编译版本：nncase 2.11.0
- 显示方式：CanMV IDE 虚拟显示 `Display.VIRT`

| 模型 | 验证集 mAP50 | 验证集 mAP50-95 | 板端平均 FPS | KPU 推理 | Python 后处理 |
|---|---:|---:|---:|---:|---:|
| 320 双模型（车辆+人物） | 0.758（车辆） | 0.442（车辆） | 约 12.8（合计） | 约 29 ms（车辆） | 约 0.9 ms（车辆） |
| 640 | 0.817 | 0.493 | 约 9.1 | 约 98 ms | 约 2.7 ms |

结论：

- **默认使用 320 版**，实时性明显更好。
- 640 版可以运行，精度更高，但帧率约 9 FPS，适合精度优先、速度其次的场景。
- 两个模型均已成功加载，摄像头采集、KPU 推理、检测后处理、风险判断和报警调用链路均正常。

## 2. 板上文件

开发板 `/sdcard/rear_vehicle/` 中已经放入：

```text
labels.txt
rear_vehicle_yolo11.py
rear_vehicle_yolo11_640.py
best_320.kmodel
best_640.kmodel
```

320 程序读取：

```text
/sdcard/rear_vehicle/best_320.kmodel
```

640 程序读取：

```text
/sdcard/rear_vehicle/best_640.kmodel
```

## 3. 显示模式

主程序默认使用 CanMV IDE 虚拟帧缓冲：

```python
DISPLAY_MODE = "virt"
```

使用板载 ST7701 LCD 时改成：

```python
DISPLAY_MODE = "lcd"
```

使用 HDMI 时改成：

```python
DISPLAY_MODE = "hdmi"
```

## 4. 串口运行与日志

程序每 30 帧打印一次统计：

```text
STATS FPS=13.7 DET=1 RISK=2 ms(cap=3.5,pre=1.0,kpu=29.4,post=0.9,risk=0.1,draw=0.7,show=0.5)
```

含义：

- `FPS`：实际处理帧率
- `DET`：当前检测目标数量
- `RISK`：0 安全、1 注意、2 危险
- `cap`：摄像头采集
- `pre`：AI2D 预处理
- `kpu`：NPU 推理
- `post`：检测框解码和 NMS
- `risk`：跟踪、测距和风险判断
- `draw/show`：OSD 绘制和显示

## 5. 可调参数

```python
CONFIDENCE_THRESHOLD = 0.40
NMS_THRESHOLD = 0.40
SAFE_DISTANCE_M = 25.0
DANGER_DISTANCE_M = 10.0
HORIZONTAL_FOV_DEG = 120.0
```

测距公式：

```text
距离 = 焦距像素 × 车辆真实宽度 / 检测框像素宽度
```

车辆宽度和 120° 视场角是初始估计值。正式使用前必须用实际相机、实际安装角度和真实车辆进行调整。

## 6. 报警逻辑

- 安全：距离大于 25 m，无报警。
- 注意：距离 10~25 m 且车辆正在接近，短鸣。
- 危险：距离小于 10 m，高频鸣叫。
- 蜂鸣器使用 `YbBuzzer`，没有阻塞摄像头主循环。

## 7. 已优化项

初版 Python 后处理每帧遍历 `2100 × 6` 次，单帧约 117 ms，帧率只有约 5 FPS。

现改为：

1. `ulab.numpy.max()` 向量化计算最佳置信度。
2. `ulab.numpy.argmax()` 向量化计算类别。
3. `ulab.numpy.nonzero()` 只取出超过阈值的候选框。
4. 最后只对少量候选框执行 NMS。

后处理降到约 0.9 ms，纯车辆阶段 320 版约 18~20 FPS；加入人物模型后双模型约 12.8 FPS。

## 8. 人物检测

320 自动启动版本现在同时运行两个模型：

- `best_320.kmodel`：检测 bus、car、microbus、motorbike、pickup-van、truck。
- `person_320.kmodel`：来自 COCO 预训练 YOLO11n，只保留 `person` 类别。

人物模型基于 COCO128 的 `person` 类验证结果：

- mAP50：约 0.531
- mAP50-95：约 0.407

双模型在 K230 1G 板上实测约 12.8 FPS。日志会分别显示：

```text
STATS FPS=9.84 DET=1 VEH=1 PERSON=0 RISK=2
```

其中：

- `VEH`：车辆数量
- `PERSON`：人物数量
- `person` 同时使用约 0.8 m 宽度和 1.7 m 高度测距，40 m 内提示，15 m 内危险

640 版本仍为纯车辆模型，不参与当前自动启动。
## 9. 开机自动启动

开发板根目录已经写入：

```text
/sdcard/main.py
```

`main.py` 会自动加载：

```text
/sdcard/rear_vehicle/rear_vehicle_yolo11.py
```

因此断开电源后重新上电，无需打开 IDE，也不需要手动运行脚本，系统会自动：

1. 初始化摄像头。
2. 加载 `best_320.kmodel`。
3. 开始车辆识别。
4. 根据风险等级控制蜂鸣器。

软重启实测输出：

```text
AUTOSTART: rear vehicle recognition
rear vehicle ready: /sdcard/rear_vehicle/best_320.kmodel display: virt
STATS FPS=18.7 DET=1 RISK=2
```

## 10. 如何关闭自动启动

删除或重命名开发板根目录的：

```text
/sdcard/main.py
```

再次上电后就不会自动运行识别程序。不要删除 `/sdcard/rear_vehicle/`，那里保存模型和主程序。




## 11. 蜂鸣器修正

蜂鸣器原实现会阻塞主循环，且 2600 Hz 音调不够响。现改为：

- 频率：2700 Hz
- 占空比：50（有效方波）
- 注意：鸣叫 180 ms，每 700 ms 重复
- 危险：鸣叫 240 ms，每 220 ms 重复
- PWM 全程非阻塞，识别循环继续运行



## 12. 人物输出解析修正

- 84 通道人物模型按张量形状自动转置，避免把坐标当成置信度。
- 人物模型直接读取第 0 类 person 分数，不再和其他 79 类比较后再过滤。
- 人物置信度阈值调整为 0.20。
- 人物风险需要连续 2 帧确认。
- 开机前 1.2 秒不报警，避免启动瞬间误报。


## 13. 当前蜂鸣器策略

当前最终版本设置为：

`python
ENABLE_PERSON_BUZZER = True`nENABLE_VEHICLE_BUZZER = False
` 

摄像头、车辆检测、人物检测和开机自动启动都会继续运行；车辆风险只显示不蜂鸣，检测到 person 时才会蜂鸣。

如需让车辆也蜂鸣，把 ENABLE_VEHICLE_BUZZER 改为 True。



## 14. 实时画面显示验证

当前最终版本使用板载 ST7701 LCD，屏幕分辨率为 800×480。开机自动启动后，屏幕上会实时显示：

- 摄像头原始画面
- 车辆和人物检测框
- 类别、置信度和估算距离
- 当前风险状态
- 实际 FPS 约为 13.8



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

## 15. IDE 黑屏问题修复

虚拟显示改为官方双层显示方式：

- YUV 视频层：显示摄像头实时画面。
- ARGB OSD 层：叠加检测框、类别、距离和风险状态。

IDE 实测帧缓冲分辨率 `800×480`，RGB 直方图均值约为 `109/108/106`，显示刷新约 `28.6 FPS`。
