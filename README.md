# K230 后方来车识别系统

> 文档整理日期：2026-10-03  
> 适用硬件：CanMV K230 YAHBOOM 1G  
> 当前推荐运行版本：320 车辆 + 人物双模型  
> 板端代码唯一来源：`k230_deploy/board/`

## 1. 项目简介

本工程实现一套面向骑行场景的后方来车识别与预警系统，运行平台为 CanMV K230。系统通过 GC2093 CSI2 摄像头获取后方画面，使用 YOLO11n 模型的 K230 INT8 `kmodel` 执行检测，再完成跟踪、单目测距、风险分级、画面叠加和蜂鸣器报警。

当前 320 版本同时运行两个模型：

- `best_320.kmodel`：检测 `bus`、`car`、`microbus`、`motorbike`、`pickup-van`、`truck`。
- `person_320.kmodel`：检测 `person`。

640 版本仍为纯车辆版本，精度更高，但速度约 9 FPS，适合精度优先而不是实时预警优先的场景。

核心能力：

- 车辆和人物目标检测
- IoU 轻量跟踪
- 基于目标宽度或高度的单目距离估算
- 安全、注意、危险三级风险判断
- LCD、HDMI 或 CanMV IDE 虚拟显示
- YbBuzzer 非阻塞报警
- `/sdcard/main.py` 开机自动运行
- 电脑端 ONNX 导出、nncase 转换、验证和部署工具

## 2. 当前推荐方案

| 方案 | 模型 | 检测对象 | 板端实测速度 | 用途 |
|---|---|---|---:|---|
| 320 双模型 | `best_320.kmodel` + `person_320.kmodel` | 6 类车辆 + 人物 | 约 12.8 FPS | 默认，实时预警 |
| 640 纯车辆 | `best_640.kmodel` | 6 类车辆 | 约 9.1 FPS | 精度优先 |
| 原电脑端工程 | `models/best.pt`、ONNX | 6 类车辆 | 依赖电脑 | 训练、验证、导出 |

推荐先部署 320 版本。正式参数仍需根据实际相机、安装角度和真实车辆宽度重新标定。

## 3. 板端文件布局

推荐将 SD 卡设置为：

```text
/sdcard/
├── main.py                         # 可选：开机自动运行入口
└── rear_vehicle/
    ├── best_320.kmodel             # 320 车辆模型
    ├── person_320.kmodel           # 320 人物模型
    ├── labels.txt                  # 车辆 + person 标签
    ├── rear_vehicle_yolo11.py      # 320 双模型主程序
    ├── best_640.kmodel             # 可选：640 车辆模型
    └── rear_vehicle_yolo11_640.py  # 可选：640 纯车辆程序
```

如果只使用 320 版本，必须复制：

```text
best_320.kmodel
person_320.kmodel
labels.txt
rear_vehicle_yolo11.py
```

如果还要使用 640 版本，再额外复制：

```text
best_640.kmodel
rear_vehicle_yolo11_640.py
```

不能把 `best_320.kmodel` 配到 640 程序，也不能让 320 程序读取 `best_640.kmodel`。程序中的 `KMODEL_PATH` 必须与实际文件名一致。

## 4. 快速部署

### 4.1 准备环境

- CanMV K230 YAHBOOM 1G
- GC2093 CSI2 摄像头
- 可启动的 CanMV K230 SD 卡
- CanMV IDE K230
- USB 数据线

### 4.2 复制文件

1. 启动 K230，使用 USB 连接电脑。
2. Windows 文件资源管理器中通常会出现 `CanMV` 便携式设备。
3. 进入 `CanMV/sdcard`。
4. 将当前最新版文件从本工程的 `k230_deploy/board/` 和 `k230_deploy/kmodel/` 复制到 `/sdcard/rear_vehicle/`。
5. 当前 320 源文件比 `rear_vehicle_k230_320.zip` 更新，发布或演示前应以 `k230_deploy/board/rear_vehicle_yolo11.py` 为准，不要直接依赖旧 ZIP。
6. 等待文件写入完成后再拔线或断电。

### 4.3 在 CanMV IDE 中运行

1. 在 CanMV IDE 中停止当前正在运行的脚本。
2. 打开 `/sdcard/rear_vehicle/rear_vehicle_yolo11.py`。
3. 确认关键配置：

```python
KMODEL_PATH = "/sdcard/rear_vehicle/best_320.kmodel"
PERSON_KMODEL_PATH = "/sdcard/rear_vehicle/person_320.kmodel"
MODEL_INPUT_SIZE = 320
RGB888P_SIZE = [320, 320]
DISPLAY_MODE = "virt"
```

4. 点击运行。正常时串口会出现类似输出：

```text
rear vehicle ready: /sdcard/rear_vehicle/best_320.kmodel person: /sdcard/rear_vehicle/person_320.kmodel person_buzzer: True vehicle_buzzer: False display: virt
STATS FPS=... DET=... VEH=... PERSON=... RISK=... BUZZ=... DETAILS=...
```

## 5. 运行逻辑

每一帧依次执行：

1. 摄像头采集 RGB888P 图像。
2. 车辆模型预处理与 KPU 推理。
3. 车辆检测解码、类别阈值过滤和 NMS。
4. 人物模型预处理与 KPU 推理。
5. 只读取 COCO 模型中的 `person` 类分数并过滤。
6. 合并检测框，执行 IoU 跟踪。
7. 估算距离、接近速度和风险等级。
8. 在画面上绘制检测框、类别、置信度、距离和风险状态。
9. 根据当前策略更新蜂鸣器。

车辆和人物模型是顺序执行的，不是两个 KPU 并行执行。320 双模型速度约 12.8 FPS，适合作为默认版本。

### 5.1 风险判断

车辆默认参数：

| 状态 | 条件 | 蜂鸣器 |
|---|---|---|
| 安全 | 距离大于 25 m，或无接近趋势 | 不响 |
| 注意 | 距离 10~25 m 且接近速度不低于 0.2 m/s | 当前默认不响 |
| 危险 | 距离不大于 10 m | 当前默认不响 |

人物默认参数：

| 状态 | 条件 | 蜂鸣器 |
|---|---|---|
| 安全 | 距离大于 40 m | 不响 |
| 注意 | 距离 15~40 m | 注意音 |
| 危险 | 距离不大于 15 m | 危险音 |

为避免单帧误报，风险需要连续 2 帧确认。程序启动前 1.2 秒也会静默。

### 5.2 当前蜂鸣器策略

当前 320 源码中的设置为：

```python
ENABLE_PERSON_BUZZER = True
ENABLE_VEHICLE_BUZZER = False
```

也就是：

- 车辆检测和风险显示继续工作。
- 车辆风险不触发蜂鸣。
- 检测到人物时按照注意或危险等级触发蜂鸣。

如果车辆也需要蜂鸣，将 `ENABLE_VEHICLE_BUZZER` 改为 `True`。注意音为 2700 Hz，每 700 ms 触发一次，每次 180 ms；危险音每 220 ms 触发一次，每次 240 ms。

## 6. 显示模式

当前 320 主程序默认使用 CanMV IDE 虚拟显示：

```python
DISPLAY_SIZE = [320, 320]
DISPLAY_MODE = "virt"
```

可选模式：

```python
DISPLAY_MODE = "virt"   # CanMV IDE
DISPLAY_MODE = "lcd"    # 板载 LCD
DISPLAY_MODE = "hdmi"   # HDMI 显示
```

注意：

- 当前 320 最终默认参数针对 `virt` 模式。
- 工程报告中有 800×480 ST7701 LCD 和 IDE 虚拟帧缓冲的上板记录。
- 如果切换 LCD 或 HDMI，应根据实际屏幕分辨率和 CanMV PipeLine 要求调整 `DISPLAY_SIZE`，切换后必须重新实机验证。
- 当前 640 程序默认 `DISPLAY_SIZE = [800, 480]`，640 版本使用独立显示管线。

## 7. 开机自动启动

`k230_deploy/board/main.py` 是自动启动入口，应复制到：

```text
/sdcard/main.py
```

它会导入：

```text
/sdcard/rear_vehicle/rear_vehicle_yolo11.py
```

并调用其 `main()`。上电后串口预期输出：

```text
AUTOSTART: rear vehicle recognition
rear vehicle ready: ...
```

关闭自动启动的方法：

- 删除 `/sdcard/main.py`，或将文件改名为 `main.py.bak`。
- 不要删除 `/sdcard/rear_vehicle/`，否则模型和主程序会一并丢失。
- 如果启动失败，程序会尝试写入 `/sdcard/rear_vehicle/boot_error.txt`。

## 8. 参数调整

320 主程序中常用的参数位于文件开头：

```python
CONFIDENCE_THRESHOLD = 0.40
NMS_THRESHOLD = 0.40

SAFE_DISTANCE_M = 25.0
DANGER_DISTANCE_M = 10.0
ATTENTION_SPEED_MPS = 0.2

PERSON_SAFE_DISTANCE_M = 40.0
PERSON_DANGER_DISTANCE_M = 15.0
PERSON_HEIGHT_M = 1.7

RISK_CONFIRM_FRAMES = 2
STARTUP_GRACE_MS = 1200
```

车辆类别还会使用单独的最低置信度：

```python
CLASS_MIN_CONFIDENCE = {
    0: 0.65,  # bus
    1: 0.45,  # car
    2: 0.50,  # microbus
    3: 0.45,  # motorbike
    4: 0.60,  # pickup-van
    5: 0.65,  # truck
    6: 0.20,  # person
}
```

车辆宽度默认值：

| 类别 | 宽度假设 |
|---|---:|
| bus | 2.5 m |
| car | 1.8 m |
| microbus | 2.0 m |
| motorbike | 0.8 m |
| pickup-van | 2.0 m |
| truck | 2.5 m |
| person | 0.8 m 宽 / 1.7 m 高 |

测距公式：

```text
distance = focal_length_px × target_real_size / target_pixel_size
```

`focal_length_px` 根据 120° 水平视场角和输入宽度估算。以上参数是初始工程值，不是安全认证参数。

## 9. 640 版本

640 版文件：

```text
/sdcard/rear_vehicle/best_640.kmodel
/sdcard/rear_vehicle/rear_vehicle_yolo11_640.py
```

640 程序只检测六类车辆，不检测人物，默认蜂鸣器频率为 1800 Hz / 2600 Hz。640 版适合验证精度，不建议在 K230 1G 上作为高帧率实时预警默认版本。

模型指标：

| 指标 | 320 车辆 | 640 车辆 |
|---|---:|---:|
| Precision | 0.7707 | 0.8148 |
| Recall | 0.7056 | 0.7613 |
| mAP50 | 0.7580 | 0.8168 |
| mAP50-95 | 0.4416 | 0.4928 |
| 板端 FPS | 纯车辆约 18~20；双模型约 12.8 | 约 9.1 |
| KPU 推理 | 约 29 ms | 约 98 ms |

## 10. 模型与训练资料

主要文件：

| 文件 | 作用 |
|---|---|
| `models/best.pt` | 自定义六类车辆训练的 PyTorch 权重 |
| `models/yolo11n_coco.pt` | COCO YOLO11n 权重，用于提取 person 类 |
| `onnx/best_320.onnx` | 320 车辆固定输入 ONNX |
| `onnx/best_640.onnx` | 640 车辆固定输入 ONNX |
| `onnx/person_320.onnx` | 320 人物固定输入 ONNX |
| `kmodel/best_320.kmodel` | K230 320 车辆 INT8 模型 |
| `kmodel/best_640.kmodel` | K230 640 车辆 INT8 模型 |
| `kmodel/person_320.kmodel` | K230 320 人物 INT8 模型 |

ONNX 输入输出已检查：

```text
best_320.onnx    input [1,3,320,320]   output [1,10,2100]
best_640.onnx    input [1,3,640,640]   output [1,10,8400]
person_320.onnx  input [1,3,320,320]   output [1,84,2100]
```

车辆验证集：

- 1046 张图片
- 6014 个实例
- 类别：bus、car、microbus、motorbike、pickup-van、truck
- 数据来源记录：Roboflow `lynkeus/vehicle-detection-mgjdd` v3，CC BY 4.0

人物模型：

- 使用 COCO 预训练 YOLO11n。
- 使用 COCO128 补充验证 `person` 类。
- 报告记录的 person mAP50 约 0.531，mAP50-95 约 0.407。

## 11. 电脑端转换流程

转换环境位于：

```text
k230_deploy/.venv_deploy/
```

主要版本：

```text
ultralytics 8.3.253
nncase 2.11.0
nncase-kpu 2.11.0
onnx 1.23.1
onnxruntime 1.22.1
```

Windows 下 nncase 对中文路径兼容较差，工程使用：

```text
C:\Users\29813\Desktop\k230识别\k230_deploy
        ↓
C:\k230_deploy
```

转换前设置：

```powershell
$env:DOTNET_ROOT = "C:\k230_deploy\tools\dotnet7"
$env:PATH = "$env:DOTNET_ROOT;$env:PATH"
$env:NNCASE_PLUGIN_PATH = "C:\k230_deploy\.venv_deploy\Lib\site-packages\nncase\modules\kpu"
```

主要脚本：

```powershell
python tools\export_onnx.py --sizes 320 640

python tools\convert_kmodel.py `
  --onnx C:\k230_deploy\onnx\best_320.onnx `
  --output C:\k230_deploy\kmodel\best_320.kmodel `
  --calibration-dir C:\k230_deploy\dataset\valid\images `
  --samples 200 `
  --input-size 320

python tools\validate_onnx.py `
  --models ..\onnx\best_320.onnx ..\onnx\best_640.onnx `
  --imgsz 320 640
```

KMODEL 转换使用 `target = "k230"`、INT8、KLD 校准、`swapRB = False`，因为板端 AI2D 输入是 RGB。

## 12. 目录说明

```text
k230识别/
├── README.md                         # 本文档
├── cam_preview.py                    # 单独测试摄像头
├── text.py                           # 蜂鸣器基础测试
├── voice.py                          # 蜂鸣器音量/旋律测试
├── voice - 副本.py                   # 另一份蜂鸣器测试
├── canmv_ide_live.jpg                # CanMV IDE 实时画面截图
├── copy_dialog.jpg                   # IDE 复制提示截图
├── reload_dialog.jpg                 # IDE 重载提示截图
├── 后方来车.zip                      # 原始资料/文档/第三方参考工程，不部署
└── k230_deploy/
    ├── README.md                     # 部署包说明，部分内容早于最终代码
    ├── board/                        # 最新板端源码
    ├── config/                       # 数据集和电脑端配置
    ├── dataset/                      # 车辆验证集（当前主要是 valid）
    ├── datasets/coco128/             # 人物模型验证数据
    ├── kmodel/                       # 三个 K230 模型
    ├── models/                       # PyTorch/ONNX 权重
    ├── onnx/                         # 固定输入 ONNX
    ├── package/                      # 已展开的部署目录
    ├── reports/                      # 验证报告和哈希清单
    ├── tools/                        # 导出、转换、验证、调试脚本
    ├── rear_vehicle_k230_320.zip     # 320 旧版打包，需按最新 board 重建
    └── rear_vehicle_k230_640.zip     # 640 打包
```

不需要复制到板子的内容：

- `.venv_deploy/`
- `tools/`
- `dataset/`、`datasets/`
- `models/`、`onnx/`
- `runs/`
- `reports/`
- `后方来车.zip`
- 训练和参考工程源码

## 13. 版本一致性检查

整理本文档时发现并确认：

| 文件 | 当前状态 |
|---|---|
| `board/rear_vehicle_yolo11.py` | 最新版，710 行，SHA-256 `A802E89145B2121219294E9D5D4217BDF479D6A3F4A08EB918E9E23025A976B0` |
| `package/rear_vehicle_320/rear_vehicle_yolo11.py` | 旧版，690 行，与最新 board 不一致 |
| `rear_vehicle_k230_320.zip` | 旧版，内含脚本 SHA-256 `101E9F51F0A4F00170550902E879C2C9CC8E7CE8D62A9FBFC86AE1510A22D588` |
| `board/rear_vehicle_yolo11_640.py` | 640 最新版，与 package/zip 一致 |
| `best_320.kmodel` | 源目录、package、report 中的哈希一致 |
| `person_320.kmodel` | 源目录与 package 哈希一致 |
| `best_640.kmodel` | 源目录、package、report 中的哈希一致 |
| `labels.txt` | 当前为 7 行，最后一行是 `person` |

因此：

- **320 部署 ZIP 目前不能视为最新完整交付包。**
- 发布或上板时优先使用 `k230_deploy/board/` 中的最新源码。
- 如果必须发 ZIP，应先重新打包 `board/`、`kmodel/`、`labels.txt` 和最新说明。
- `reports/manifest.json` 记录的是 20:42 版本，未包含 21:42 后对 320 源码的修改。
- `reports/board_test.md` 中的历史性能数据仍可参考，但最新 320 源码修改后应再跑一次实机确认。

本次整理时桌面没有检测到已连接的 CanMV USB 设备，也没有运行中的 CanMV IDE，因此没有覆盖或重新读取当前 SD 卡，也没有在整理过程中重新启动识别程序。

## 14. 常见问题

### 提示找不到 KMODEL

检查模型文件名、目录和脚本中的 `KMODEL_PATH`。320 需要 `best_320.kmodel`，640 需要 `best_640.kmodel`。

### 人物模型加载失败

确认 `person_320.kmodel` 已复制到 `/sdcard/rear_vehicle/`，并与 `PERSON_KMODEL_PATH` 完全一致。

### 有检测框但没有图像

先使用默认 `DISPLAY_MODE = "virt"` 验证。不要在未重新验证的情况下直接套用其他版本的显示参数。参考 `canmv_ide_live.jpg` 和 `reports/board_test.md` 中的显示记录。

### 车辆有危险框但蜂鸣器不响

这是当前设计。`ENABLE_VEHICLE_BUZZER = False`，只有人物报警默认开启。需要车辆报警时改成 `True`。

### 蜂鸣器一直不响

检查板端 `ybUtils/YbBuzzer.py`、`YbBuzzer` 初始化和 `ENABLE_PERSON_BUZZER` 设置。程序在没有 YbBuzzer 时仍会继续检测，但不会发声。

### 串口被占用

COM 端口同一时间只能由一个程序打开。关闭串口助手，或在另一个程序中停止正在运行的脚本。

### 自动启动后无法查看文件

先关闭电源，插拔 USB，等待设备重新出现后再访问 MTP。不要在程序运行时直接拔 SD 卡。

### 640 版本速度太低

这是预期现象。K230 1G 上 640 的 KPU 推理约 98 ms，优先使用 320 双模型版本。

## 15. 测试与验收边界

已经完成的验证：

- 车辆模型训练权重、ONNX 和 KMODEL 产物存在。
- 320/640 车辆模型完成验证集评估。
- person 模型完成 COCO128 的 person 类评估。
- 工程报告记录了摄像头、KPU、后处理、报警和显示链路实机运行结果。
- 320 双模型报告速度约 12.8 FPS。
- 640 纯车辆报告速度约 9.1 FPS。

仍需完成：

- 最新一次 320 源码修改后的重新上板验证。
- 实际镜头、安装角度和车辆宽度标定。
- 夜间、逆光、雨天和反光场景测试。
- 真实骑行条件下的误报、漏报和预警距离测试。
- 报警声在骑行风噪环境中的可听度验证。

本系统只能作为辅助预警，不能替代骑行者观察和判断。当前距离与风险阈值属于工程估计值，不应作为安全认证或事故责任判断依据。