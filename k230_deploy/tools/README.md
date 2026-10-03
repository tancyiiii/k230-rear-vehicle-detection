# 转换工具说明

Windows 上 nncase 对含中文的工程路径兼容性不好。本工作区使用了 ASCII 目录映射：

```text
C:\k230_deploy  ->  C:\Users\29813\Desktop\k230识别\k230_deploy
```

转换环境必须设置：

```powershell
$env:DOTNET_ROOT = "C:\k230_deploy\tools\dotnet7"
$env:PATH = "$env:DOTNET_ROOT;$env:PATH"
$env:NNCASE_PLUGIN_PATH = "C:\k230_deploy\.venv_deploy\Lib\site-packages\nncase\modules\kpu"
```

## 已执行流程

```powershell
python tools\export_onnx.py --sizes 320 640

python tools\convert_kmodel.py `
  --onnx C:\k230_deploy\onnx\best_320.onnx `
  --output C:\k230_deploy\kmodel\best_320.kmodel `
  --calibration-dir C:\k230_deploy\dataset\valid\images `
  --samples 200 `
  --input-size 320

python tools\convert_kmodel.py `
  --onnx C:\k230_deploy\onnx\best_640.onnx `
  --output C:\k230_deploy\kmodel\best_640.kmodel `
  --calibration-dir C:\k230_deploy\dataset\valid\images `
  --samples 100 `
  --input-size 640
```

关键转换设置：

- `target = "k230"`
- `preprocess = True`
- `swapRB = False`，因为板端 AI2D 输入是 RGB
- `input_type = "uint8"`
- `input_range = [0, 1]`
- `mean = [0, 0, 0]`
- `std = [1, 1, 1]`

`nncase-kpu 2.11.0` 不是普通 PyPI 包，需要从勘智 GitHub Release 下载 Windows 版插件：

https://github.com/kendryte/nncase/releases/tag/v2.11.0
