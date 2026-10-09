# -*- coding: utf-8 -*-
"""生成 K230 YOLO11n 双模型部署技术文档。"""

from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "k230_deploy" / "reports" / "YOLO11n_K230_dual_model_deployment_technical_doc.docx"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    run.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if color:
        run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_width(cell, width_cm):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))
    tc_w.set(qn("w:type"), "dxa")


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    new_run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.text = text
    new_run.append(text_node)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def add_para(doc, text="", style=None, bold_prefix=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(6)
    if bold_prefix and text.startswith(bold_prefix):
        r = p.add_run(bold_prefix)
        r.bold = True
        p.add_run(text[len(bold_prefix):])
    else:
        p.add_run(text)
    return p


def add_bullets(doc, items, level=0):
    for item in items:
        p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
        p.paragraph_format.left_indent = Cm(0.65 + level * 0.55)
        p.paragraph_format.space_after = Pt(2)
        p.add_run(item)


def add_numbered(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(2)
        p.add_run(item)


def add_code(doc, language, code):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.45)
    p.paragraph_format.right_indent = Cm(0.45)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(7)
    run = p.add_run("代码语言：" + language + "\n" + code.strip("\n"))
    run.font.name = "Consolas"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(31, 41, 55)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "F3F4F6")
    pPr.append(shd)
    return p


def add_callout(doc, label, text, fill="FFF2CC"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(label + "\n")
    r.bold = True
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    p.add_run(text)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, head in enumerate(headers):
        set_cell_text(hdr.cells[i], head, bold=True, color=(255, 255, 255))
        set_cell_shading(hdr.cells[i], "1F4E78")
        if widths:
            set_cell_width(hdr.cells[i], widths[i])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
            if widths:
                set_cell_width(cells[i], widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def chapter(doc, title):
    doc.add_heading(title, level=1)


def section(doc, title):
    doc.add_heading(title, level=2)


def sub_section(doc, title):
    doc.add_heading(title, level=3)


def configure_document(doc):
    sec = doc.sections[0]
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.3)
    sec.right_margin = Cm(2.3)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    normal.font.size = Pt(10.5)
    for name, size, color in (("Title", 24, "17365D"), ("Heading 1", 16, "17365D"), ("Heading 2", 13, "1F4E78"), ("Heading 3", 11, "365F91")):
        style = styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("CanMV K230 YOLO11n 双模型部署技术文档  |  ")
    add_page_number(footer)


def add_cover(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Cm(2.0)
    p.paragraph_format.space_after = Cm(1.0)
    r = p.add_run("基于 CanMV K230 YAHBOOM 1G 的\nYOLO11n 双模型部署")
    r.bold = True
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    r.font.size = Pt(24)
    r.font.color.rgb = RGBColor(23, 54, 93)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Cm(2.0)
    r = p2.add_run("后方车辆与行人识别预警技术文档")
    r.font.size = Pt(16)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    r.font.color.rgb = RGBColor(31, 78, 121)
    add_table(doc, ["文档属性", "内容"], [
        ("目标硬件", "CanMV K230 YAHBOOM 1G"),
        ("摄像头", "GC2093 CSI2"),
        ("固件", "CanMV IDE 0.4.0"),
        ("转换工具", "nncase 2.11.0 / nncase-kpu 2.11.0"),
        ("板端运行时", "CanMV MicroPython"),
        ("文档依据", "当前 board 源码、配置、验证报告和可见工程文件"),
        ("编制日期", "2026-10-09"),
    ], [4.0, 10.5])
    add_callout(doc, "📌 设计决策说明", "本文以 k230_deploy/board/ 中当前源码为板端实现的最高优先级依据。README、package、ZIP 和 reports/manifest.json 如果与当前源码冲突，只作为历史版本或辅助证据，并在正文中明确标记。", "DDEBF7")
    doc.add_page_break()


def add_toc(doc):
    doc.add_heading("目录", level=1)
    chapters = [
        "第 1 章 项目概述", "第 2 章 工程目录与环境准备", "第 3 章 数据集与标注",
        "第 4 章 YOLO11n 训练、导出与 KMODEL 转换", "第 5 章 MicroPython 板端部署",
        "第 6 章 后方车辆与行人风险判断", "第 7 章 测试与验证", "第 8 章 性能与资源分析",
        "第 9 章 C++ RTOS 方案现状与后续规划", "第 10 章 总结与扩展",
    ]
    for item in chapters:
        add_para(doc, item)
    add_callout(doc, "⚠️ 注意", "Word 打开后可以使用“引用→更新目录”生成带页码的自动目录。本版本保留章节顺序和标题层级，正文内容已完整写入。", "FFF2CC")
    doc.add_page_break()


def write_doc():
    doc = Document()
    configure_document(doc)
    add_cover(doc)
    add_toc(doc)

    doc.add_heading("文档范围与事实边界", level=1)
    add_para(doc, "本文描述一个已经在 CanMV K230 YAHBOOM 1G 上进行过实机验证的 MicroPython 视觉预警系统。系统从 GC2093 CSI2 摄像头取得后方画面，使用车辆 YOLO11n KMODEL 和 COCO 预训练 YOLO11n 人物 KMODEL 进行串行推理，再将检测结果交给轻量 IoU 跟踪、单目测距和三级风险控制逻辑。本文同时记录模型转换、板端部署、显示、语音、蜂鸣器和 UART1 控制。")
    add_para(doc, "文中所有“已实现”“已验证”“实测”均限定在当前工程证据范围内。当前仓库的正式目录缺少若干 640 产物，而历史报告和 manifest 仍记录这些文件，因此涉及 640 的部分会区分“报告中已验证”和“当前工作树可直接复现”两种含义。")

    chapter(doc, "第 1 章 项目概述")
    section(doc, "1.1 项目目标")
    add_para(doc, "项目目标是在自行车、低速移动平台或其他后视监测场景中，利用一块 CanMV K230 YAHBOOM 1G 和 GC2093 CSI2 摄像头，对后方车辆和行人进行实时检测，并根据检测框估算距离、连续帧距离变化和目标类别输出安全、注意、危险三级状态。系统不把“目标被检测到”直接等价为“目标正在驶来”，而是使用跟踪后距离变化计算接近速度，并通过连续帧确认抑制瞬态误报。")
    section(doc, "1.2 应用场景")
    add_bullets(doc, [
        "骑行者后方来车提示：车辆进入约 25 m 范围且被判断为接近时进入注意状态，约 10 m 内进入危险状态。",
        "后方行人提示：人物采用独立 COCO person 模型，默认约 40 m 内提示、约 15 m 内危险。",
        "开发验证：CanMV IDE 虚拟显示可显示摄像头画面和 OSD；正式设备可选择 LCD 或 HDMI。",
        "外部设备控制：通过 UART1 的 0x01/0x00 指令启停取帧、推理和报警。",
    ])
    section(doc, "1.3 硬件与软件环境")
    add_table(doc, ["项目", "当前配置", "说明"], [
        ("开发板", "CanMV K230 YAHBOOM 1G", "本文不泛化到未经验证的其他 K230 板卡"),
        ("图像传感器", "GC2093 CSI2", "板端源码使用 Sensor(id=2)"),
        ("固件/IDE", "CanMV IDE 0.4.0", "报告记录的实机验证版本"),
        ("推理运行时", "CanMV MicroPython + nncase_runtime", "板端加载 KMODEL"),
        ("模型转换", "nncase 2.11.0 + nncase-kpu 2.11.0", "target 为 k230"),
        ("默认 AI 输入", "320×320 RGB888P", "车辆和人物默认串行推理"),
        ("默认显示", "800×480，DISPLAY_MODE=virt", "支持虚拟显示、LCD、HDMI"),
    ], [3.0, 5.2, 6.3])
    add_callout(doc, "⚠️ 注意", "OV5647 只在工程内的 SDK 资料中作为潜在兼容传感器出现，当前实测摄像头是 GC2093 CSI2。若更换 OV5647，必须根据实际 SDK、排线、Sensor ID 和硬件时序重新确认。", "FFF2CC")
    section(doc, "1.4 双模型系统架构")
    add_para(doc, "320 版本每帧先运行车辆模型，再对同一帧运行人物模型。车辆模型输出六类车辆，人物模型来自 COCO 预训练 YOLO11n，但通过 target_class_index=0 只保留 person 类。两类检测结果合并后进入同一个跟踪和风险控制器。640 版本当前只对应车辆模型，不能写成 640 双模型。")
    add_code(doc, "text", "摄像头 Sensor(id=2)\n  ├─ chn0：YUV 视频层 → Display.LAYER_VIDEO1\n  └─ chn2：RGB888P 320×320 → AI2D → KPU\n                         ├─ best_320.kmodel（6 类车辆）\n                         └─ person_320.kmodel（只取 person）\n                                  ↓\n                    解析 → 过滤 → NMS → IoU 跟踪\n                                  ↓\n                    单目测距 → 接近速度 → 风险等级\n                         ├─ ARGB OSD\n                         ├─ YbBuzzer\n                         ├─ YbSpeaker + PCM\n                         └─ UART1 状态控制")
    section(doc, "1.5 能力边界")
    add_para(doc, "系统当前识别的是目标类别、估算距离和接近风险，而不是显式识别车辆行驶方向。工程没有实现车道线、光流、光流方向分类、车辆姿态分类或基于多摄像头的三维速度估计。距离是基于水平视场角、目标真实宽度/高度和检测框像素尺寸的单目近似值，必须通过实际相机安装位置和真实车辆重新标定。")

    chapter(doc, "第 2 章 工程目录与环境准备")
    section(doc, "2.1 当前工程目录")
    add_code(doc, "text", "k230_deploy/\n├─ board/\n│  ├─ main.py\n│  ├─ rear_vehicle_yolo11.py\n│  ├─ serial_control.py\n│  ├─ labels.txt\n│  ├─ attention_person.pcm\n│  └─ attention_vehicle.pcm\n├─ models/\n│  ├─ best.pt\n│  ├─ yolo11n_coco.pt\n│  └─ yolo11n_coco.onnx\n├─ onnx/\n│  ├─ best_320.onnx\n│  └─ person_320.onnx\n├─ kmodel/\n│  ├─ best_320.kmodel\n│  ├─ person_320.kmodel\n│  └─ best_320_test_DO_NOT_USE.kmodel\n├─ config/\n│  ├─ dataset.yaml\n│  └─ gpu_train_args.yaml\n├─ dataset/valid/images/\n├─ datasets/coco128/\n├─ reports/\n└─ tools/\n   ├─ export_onnx.py\n   └─ convert_kmodel.py")
    add_para(doc, "board/ 是当前板端实现的唯一主要依据。package/rear_vehicle_320/ 是部署快照，tools/reference_yolo11/ 是参考转换资料，reports/ 是验证和状态记录，不能在内容冲突时取代当前板端源码。")
    section(doc, "2.2 板端 SD 卡目录")
    add_code(doc, "text", "/sdcard/main.py\n/sdcard/rear_vehicle/rear_vehicle_yolo11.py\n/sdcard/rear_vehicle/serial_control.py\n/sdcard/rear_vehicle/best_320.kmodel\n/sdcard/rear_vehicle/person_320.kmodel\n/sdcard/rear_vehicle/labels.txt\n/sdcard/rear_vehicle/attention_person.pcm\n/sdcard/rear_vehicle/attention_vehicle.pcm")
    add_para(doc, "main.py 延时约 1.2 秒后把 /sdcard/rear_vehicle 插入 sys.path，导入 rear_vehicle_yolo11 并调用 app.main()。应用目录或入口文件缺失时写入 /sdcard/boot_error.txt 或应用目录下的 boot_error.txt。")
    section(doc, "2.3 ASCII 转换目录")
    add_para(doc, "Windows 上 nncase 对含中文路径的兼容性不稳定。工程工具说明使用 C:\\k230_deploy 作为当前工程 k230_deploy 目录的 ASCII 映射。它不是新的逻辑工程，而是为了让转换工具访问路径时不包含中文。")
    add_code(doc, "powershell", "$env:DOTNET_ROOT = \"C:\\k230_deploy\\tools\\dotnet7\"\n$env:PATH = \"$env:DOTNET_ROOT;$env:PATH\"\n$env:NNCASE_PLUGIN_PATH = \"C:\\k230_deploy\\.venv_deploy\\Lib\\site-packages\\nncase\\modules\\kpu\"\nSet-Location C:\\k230_deploy")
    section(doc, "2.4 训练环境与可复现边界")
    add_para(doc, "dataset.yaml 和 gpu_train_args.yaml 中的训练路径指向工程外部的中文 Windows 目录。当前仓库包含 1046 张验证图片和 COCO128 的 128 张训练图片，但没有把完整车辆训练目录、全部训练源码和原始数据包作为可独立复现的训练环境。文档可以准确复述训练参数，不能宣称仅凭当前仓库即可从零重训出完全相同的 best.pt。")
    add_callout(doc, "⚠️ 注意", "k230_deploy/kmodel/ 当前可见的是 best_320.kmodel、person_320.kmodel 和一个明确标注 DO_NOT_USE 的测试模型。best_640.kmodel、onnx/best_640.onnx、board/rear_vehicle_yolo11_640.py 在 reports/manifest.json 或历史报告中有记录，但不在当前正式目录中。后续若要复现 640，必须先补齐并校验对应文件。", "FFF2CC")
    section(doc, "2.5 推荐准备步骤")
    add_numbered(doc, [
        "确认开发板是 CanMV K230 YAHBOOM 1G，接入 GC2093 CSI2，安装或确认 CanMV IDE 固件 0.4.0。",
        "将板端源码、模型、PCM 文件和 main.py 按 SD 卡目录复制。",
        "在电脑端使用 ASCII 映射目录建立 nncase 转换环境，并确认 nncase-kpu 2.11.0 插件路径。",
        "先运行 cam_preview.py 或等价预览程序确认摄像头，再运行模型程序。",
        "从 UART 日志确认 AUTOSTART、模型加载、UART1 和 STATS 输出。",
    ])

    chapter(doc, "第 3 章 数据集与标注")
    section(doc, "3.1 车辆数据集")
    add_para(doc, "车辆模型的 dataset.yaml 指向 Roboflow vehicle-detection-mgjdd v3，许可证为 CC BY 4.0。类别数 nc=6，名称顺序必须和训练、ONNX 输出解析以及 labels.txt 一致。")
    add_table(doc, ["类别索引", "类别名", "当前用途"], [
        ("0", "bus", "车辆检测和车辆宽度测距"), ("1", "car", "车辆检测和车辆宽度测距"),
        ("2", "microbus", "车辆检测和车辆宽度测距"), ("3", "motorbike", "车辆检测和车辆宽度测距"),
        ("4", "pickup-van", "车辆检测和车辆宽度测距"), ("5", "truck", "车辆检测和车辆宽度测距"),
    ], [2.5, 4.0, 8.0])
    add_para(doc, "验证集记录为 1046 张图片、6014 个实例。comparison.md 给出了 320 和 640 的 Precision、Recall、mAP50 和 mAP50-95，并给出了六类逐类 mAP50-95。该验证指标是 PC/模型验证集指标，不等同于 K230 板端实时识别准确率。")
    section(doc, "3.2 人物模型")
    add_para(doc, "人物模型文件为 models/yolo11n_coco.pt、onnx/person_320.onnx 和 kmodel/person_320.kmodel。它使用 COCO 预训练 YOLO11n，板端只保留 person 类，不将其他 COCO 类别显示或参与风险判断。报告给出的 COCO128 person 类指标约为 mAP50=0.531、mAP50-95=0.407。")
    section(doc, "3.3 数据已有项与外部项")
    add_table(doc, ["范围", "工程现状", "复现含义"], [
        ("已有", "models/best.pt、yolo11n_coco.pt、onnx/person_320.onnx、kmodel/person_320.kmodel", "可用于检查文件和部署链路"),
        ("已有", "dataset/valid/images 下 1046 张验证图片", "可用于部分验证和 KMODEL 校准"),
        ("已有", "datasets/coco128 下约 128 张样例", "用于人物模型验证参考"),
        ("外部", "dataset.yaml 的 train/valid/test 根路径", "训练数据和完整训练目录不在当前仓库"),
        ("未提供", "test_capture.py、完整采集流程", "只能把 cam_preview.py 作为预览工具"),
    ], [2.0, 6.5, 6.0])
    add_callout(doc, "📌 设计决策说明", "车辆与人物使用两个独立模型，避免把六类车辆数据与 COCO person 类强行混合训练，也便于在性能优先场景只加载车辆模型。", "DDEBF7")
    section(doc, "3.4 标注工具边界")
    add_para(doc, "X-AnyLabeling 可以作为未来新增数据的可选标注工具，但当前工程没有它的已验证标注流程、导入导出记录或完整数据闭环。后续使用时应记录类别映射、YOLO 标签格式、训练/验证划分、许可证和质量抽检结果。")

    chapter(doc, "第 4 章 YOLO11n 训练、导出与 KMODEL 转换")
    section(doc, "4.1 训练配置")
    add_para(doc, "gpu_train_args.yaml 使用 Ultralytics detect/train 配置，基础模型为 yolo11n.pt，训练轮数 150，batch=16，imgsz=640，device='0'，workers=0，pretrained=true，deterministic=true，close_mosaic=10，AMP 开启。该文件记录的是训练任务参数，不代表训练权重和完整数据均已包含在当前仓库。")
    add_code(doc, "yaml", "task: detect\nmode: train\nmodel: ...\\yolo11n.pt\ndata: ...\\train\\data.yaml\nepochs: 150\nbatch: 16\nimgsz: 640\ndevice: '0'\nworkers: 0\npretrained: true\nseed: 0\ndeterministic: true\nclose_mosaic: 10")
    section(doc, "4.2 ONNX 导出")
    add_para(doc, "export_onnx.py 读取 best.pt，使用 Ultralytics 导出固定输入 ONNX。脚本默认导出 320 和 640 两个尺寸，batch=1，dynamic=False，simplify=True，opset=13，half=False，nms=False，device='cpu'。板端后处理需要原始检测输出，因此不能把导出 NMS 写成已启用。")
    add_code(doc, "powershell", "Set-Location C:\\k230_deploy\npython tools\\export_onnx.py --sizes 320 640 --opset 13")
    add_callout(doc, "⚠️ 注意", "当前 export_onnx.py 的权重和输出命名逻辑是车辆 best.pt 专用。person_320.onnx 是工程中已有的独立产物，不能把脚本当前代码描述成已经同时导出车辆和人物两个模型。", "FFF2CC")
    section(doc, "4.3 nncase KMODEL 转换")
    add_para(doc, "convert_kmodel.py 的目标平台为 k230，启用 preprocess，输入类型 uint8，输入布局 NCHW，输出布局 NCHW，RGB 输入并设置 swapRB=False。PTQ 使用 uint8 激活和 uint8 权重，calibrate_method='Kld'，不做权重微调。校准图片由 --calibration-dir 指定，最多取 --samples 张。")
    add_code(doc, "powershell", "Set-Location C:\\k230_deploy\npython tools\\convert_kmodel.py `\n  --onnx C:\\k230_deploy\\onnx\\best_320.onnx `\n  --output C:\\k230_deploy\\kmodel\\best_320.kmodel `\n  --calibration-dir C:\\k230_deploy\\dataset\\valid\\images `\n  --samples 200 `\n  --input-size 320\n\npython tools\\convert_kmodel.py `\n  --onnx C:\\k230_deploy\\onnx\\best_640.onnx `\n  --output C:\\k230_deploy\\kmodel\\best_640.kmodel `\n  --calibration-dir C:\\k230_deploy\\dataset\\valid\\images `\n  --samples 100 `\n  --input-size 640")
    add_para(doc, "人物模型应使用相同的转换脚本、相同的 K230 target 和对应输入尺寸单独转换：")
    add_code(doc, "powershell", "Set-Location C:\\k230_deploy\npython tools\\convert_kmodel.py `\n  --onnx C:\\k230_deploy\\onnx\\person_320.onnx `\n  --output C:\\k230_deploy\\kmodel\\person_320.kmodel `\n  --calibration-dir C:\\k230_deploy\\datasets\\coco128\\images\\train2017 `\n  --samples 100 `\n  --input-size 320")
    section(doc, "4.4 输入预处理一致性")
    add_table(doc, ["项目", "导出/转换设置", "板端对应"], [
        ("颜色", "RGB，swapRB=False", "Sensor chn2 为 RGB888P，AI2D 输入 uint8"),
        ("布局", "NCHW", "AIBase/AI2D 使用 NCHW_FMT"),
        ("尺寸", "320 或 640 固定尺寸", "DetectionApp 的 model_input_size"),
        ("量化", "uint8/INT8，KLD", "KPU KMODEL 推理"),
        ("NMS", "导出阶段关闭", "Python postprocess 后执行 NMS"),
    ], [3.0, 6.0, 5.5])
    add_callout(doc, "⚠️ 注意", "convert_kmodel.py 定义了 letterbox() 辅助函数，但当前校准循环实际使用 cv2.resize 直接缩放图片，并没有调用 letterbox()。文档不能把“定义了 letterbox”写成“校准样本已实际使用 letterbox”。编译选项中的 letterbox_value=114 也不能替代对校准数据实际预处理路径的核对。", "FFF2CC")
    section(doc, "4.5 320 与 640 的工程差异")
    add_para(doc, "320 更适合双模型实时预警，车辆纯模型约 18～20 FPS，车辆+人物双模型约 12.8 FPS。640 的车辆模型在验证集上精度更高，但板端 KPU 约 98 ms，车辆帧率约 9.1 FPS；当前 640 版本不运行人物模型。报告和 manifest 记录过 640 产物，但当前正式目录缺失对应文件，后续发布必须重新核对 SHA256 和板端复制包。")

    chapter(doc, "第 5 章 MicroPython 板端部署")
    section(doc, "5.1 PipeLine 与 Sensor")
    add_para(doc, "DISPLAY_MODE 为 virt 时，当前源码使用 VirtualPipeLine：Sensor(id=2) 的 chn0 输出 YUV 视频层并绑定到 Display.LAYER_VIDEO1，chn2 输出 RGB888P 给 AI 推理，OSD 使用独立 ARGB8888 图层叠加。DISPLAY_MODE 为 lcd 或 hdmi 时使用官方 PipeLine。")
    add_code(doc, "python", "class VirtualPipeLine:\n    def create(self):\n        # 使用实际工程验证的 Sensor 实例\n        self.sensor = Sensor(id=2)\n        self.sensor.reset()\n        self.sensor.set_framesize(width=800, height=480, chn=CAM_CHN_ID_0)\n        self.sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)\n        self.sensor.set_framesize(width=320, height=320, chn=CAM_CHN_ID_2)\n        self.sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)")
    section(doc, "5.2 DetectionApp 接口")
    add_code(doc, "python", "class DetectionApp(AIBase):\n    def __init__(\n        self,\n        kmodel_path,\n        model_input_size,\n        rgb888p_size,\n        display_size,\n        class_map,\n        confidence_threshold=0.40,\n        target_class_index=None,\n        debug_mode=0,\n    ):\n        ...")
    add_table(doc, ["参数", "当前调用", "含义与调参影响"], [
        ("kmodel_path", "/sdcard/rear_vehicle/best_320.kmodel 或 person_320.kmodel", "KMODEL 文件路径；路径错误会导致模型加载失败"),
        ("model_input_size", "(320, 320)", "模型固定输入宽高；改尺寸必须重新导出和转换"),
        ("rgb888p_size", "[320, 320]", "摄像头 AI 通道尺寸；影响 AI2D 和坐标比例"),
        ("display_size", "[800, 480]", "OSD 输出尺寸；只改变显示缩放，不改变模型输入"),
        ("class_map", "车辆 0~5；人物 0→6", "模型类别到系统统一类别的映射"),
        ("confidence_threshold", "车辆 0.40；人物 0.20", "降低可提高召回但可能增加误检"),
        ("target_class_index", "车辆 None；人物 0", "人物直接取 person 分数，避免与其他 79 类竞争"),
        ("debug_mode", "0", "AI2D/AIBase 调试等级；提高会增加日志和开销"),
    ], [3.5, 4.2, 6.8])
    section(doc, "5.3 AI2D 预处理")
    add_para(doc, "config_preprocess() 使用 Ai2d.resize(tf_bilinear, half_pixel)，并以 NCHW、uint8 到 NCHW、uint8 建立从 RGB888P_SIZE 到 model_input_size 的 resize 流程。当前主程序没有直接调用 detector.run(img)，而是手动调用 preprocess、inference 和 postprocess，以便两个模型串行推理和分别统计性能。")
    section(doc, "5.4 真实双模型调用链")
    add_code(doc, "python", "frame = pipeline.get_frame()\n\n# 车辆模型\nvehicle_tensors = vehicle_detector.preprocess(frame)\nvehicle_results = vehicle_detector.inference(vehicle_tensors)\nvehicle_detections = vehicle_detector.postprocess(vehicle_results)\n\n# 人物模型：同一帧上串行执行\nperson_tensors = person_detector.preprocess(frame)\nperson_results = person_detector.inference(person_tensors)\nperson_detections = person_detector.postprocess(person_results)\n\ndetections = vehicle_detections + person_detections\ntracks = tracker.update(detections, now_ms)\ncurrent, overall_risk = risk_controller.evaluate(tracks, now_ms)\nvehicle_detector.draw_result(pipeline, draw_detections, overall_risk)\npipeline.show_image()")
    section(doc, "5.5 当前全局配置")
    add_table(doc, ["配置名", "当前值", "推荐范围/建议", "含义与调参影响"], [
        ("KMODEL_PATH", "/sdcard/rear_vehicle/best_320.kmodel", "按部署包实际路径", "车辆模型路径；错误会导致模型加载失败"),
        ("PERSON_KMODEL_PATH", "/sdcard/rear_vehicle/person_320.kmodel", "可选；存在才启用人物模型", "人物模型路径；缺失时退化为车辆模式"),
        ("MODEL_INPUT_SIZE", "320", "320；或重新转换后的 640", "模型边长；必须与 ONNX/KMODEL 固定输入一致"),
        ("RGB888P_SIZE", "[320, 320]", "与模型输入一致优先", "AI 摄像头通道尺寸；影响 AI2D 和坐标缩放"),
        ("DISPLAY_SIZE", "[800, 480]", "800×480；按屏幕 SDK 调整", "显示和 OSD 尺寸；不改变 KPU 输入"),
        ("DISPLAY_MODE", "virt", "virt/lcd/hdmi", "选择显示后端；显示路径会影响总体 FPS"),
        ("CONFIDENCE_THRESHOLD", "0.40", "0.25～0.70 起始试验", "降低提高召回但增加误检；还受类别阈值约束"),
        ("NMS_THRESHOLD", "0.40", "0.35～0.60 起始试验", "越低越容易抑制重叠框；越高可能保留重复框"),
        ("MAX_BOXES", "50", "20～100，按场景目标数", "限制 NMS 后框数量；过大增加跟踪和绘制开销"),
        ("CLASS_MIN_CONFIDENCE", "bus .65/car .45/microbus .50/motorbike .45/pickup-van .60/truck .65/person .20", "每类 0.20～0.90 单独标定", "类别级过滤；应根据验证集混淆和现场误检调整"),
        ("TRACK_IOU_THRESHOLD", "0.30", "0.20～0.50 起始试验", "低值更易保持轨迹但可能串轨；高值更严格但易断轨"),
        ("TRACK_MAX_AGE_MS", "1200", "500～2000 ms", "轨迹保留时间；过大可能保留过期目标"),
        ("HORIZONTAL_FOV_DEG", "120.0", "用标定板/实车实测", "用于估计焦距；错误会成比例影响距离"),
        ("SAFE_DISTANCE_M", "25.0", "车辆实车标定，约 15～40 m 试验", "车辆注意距离上界；过小会晚提示，过大易频繁提示"),
        ("DANGER_DISTANCE_M", "10.0", "车辆实车标定，约 5～15 m 试验", "车辆危险距离上界；必须结合刹车和场景安全策略"),
        ("PERSON_SAFE_DISTANCE_M", "40.0", "人物实车标定，约 20～50 m 试验", "人物提示距离上界；受人物尺寸和遮挡影响"),
        ("PERSON_DANGER_DISTANCE_M", "15.0", "人物实车标定，约 8～25 m 试验", "人物危险距离上界；不能直接当作安全法规值"),
        ("PERSON_HEIGHT_M", "1.7", "按目标人群约 1.4～1.9 m 校准", "人物高度先验；改变会影响高度测距"),
        ("RISK_CONFIRM_FRAMES", "2", "2～5 帧，按 FPS 和误报率调整", "连续确认帧数；越大越稳定但报警延迟越大"),
        ("STARTUP_GRACE_MS", "1200", "800～3000 ms", "启动静默时间；保护摄像头、音频和曝光初始化"),
    ], [3.6, 4.0, 4.8, 5.8])
    add_para(doc, "表中的推荐范围是现场调参起始范围，不是已经完成的安全标定结果。FOV、车辆真实宽度、人物身高、安全距离和危险距离必须在实际相机安装高度、俯仰角和目标距离下重新测量；任何调参结果都应记录测试条件和误报/漏报变化。")
    section(doc, "5.6 显示与 OSD")
    add_para(doc, "draw_result(pipeline, detections, overall_risk) 清除并重绘 ARGB OSD 图层，绘制检测框、类别、置信度、估算距离和 REAR: SAFE/ATTENTION/DANGER 状态。摄像头原图由视频层直通，解决了直接显示 RGB565 快照时 CanMV IDE 画面近黑的问题。")
    section(doc, "5.7 UART1 控制")
    add_code(doc, "python", "UART_ID = 1\nUART_TX_GPIO = 9\nUART_RX_GPIO = 10\nUART_BAUDRATE = 152000\nCMD_STOP = 0x00\nCMD_START = 0x01")
    add_para(doc, "串口格式为 8N1、无流控。GPIO9 是 TX，GPIO10 是 RX；外部 USB-TTL 需要交叉连接 TXD→GPIO10/RX、RXD→GPIO9/TX，并共地。0x00 会暂停取帧、推理和报警，0x01 恢复运行，程序不卸载模型。")
    section(doc, "5.8 报警输出")
    add_para(doc, "AlertController 同时管理 YbBuzzer 和 YbSpeaker。当前源码定义 ENABLE_PERSON_SPEAKER=True、ENABLE_VEHICLE_SPEAKER=True；语音文件为 attention_person.pcm 和 attention_vehicle.pcm，音频链路为 YbSpeaker + media.pyaudio，44100 Hz、双声道、16-bit PCM。蜂鸣器默认使用 2700 Hz、音量 100、两次短鸣，报警在后台线程执行，主推理循环不等待完整播放。")
    add_para(doc, "同一风险等级和目标类型默认 5000 ms 内不重复播放，风险消失后停止持续语音/蜂鸣。person_alert 优先选择人物提示音，只有没有人物风险时才使用车辆提示音。")

    chapter(doc, "第 6 章 后方车辆与行人风险判断")
    section(doc, "6.1 后处理与类别过滤")
    add_para(doc, "postprocess() 兼容 YOLO 输出为 (4+classes, anchors) 或 (anchors, 4+classes) 的情况，必要时进行转置。车辆模型对六类分数执行 max/argmax；人物模型通过 target_class_index=0 直接读取 person 分数。候选框经过全局置信度、类别最低置信度、框大小、特殊大框规则和 NMS 后再进入跟踪。")
    add_para(doc, "NMS 使用 IoU（Intersection over Union，交并比）衡量两个框的重叠度，按置信度从高到低保留框。当候选框与已保留框的 IoU 不小于 NMS_THRESHOLD 时抑制候选框。MAX_BOXES=50 用于限制最坏情况下的后续处理量。")
    section(doc, "6.2 IoU 跟踪")
    add_para(doc, "SimpleTracker 按类别分别匹配轨迹和当前检测，优先选择 IoU 最大且超过 0.30 的历史轨迹。匹配成功时更新 bbox、score 和 last_seen_ms；未匹配检测新建轨迹。超过 1200 ms 未见的轨迹被清除。每条轨迹保存 previous_distance_m、previous_time_ms、speed_mps、candidate_risk、risk_frames 和 risk。")
    section(doc, "6.3 单目距离估算")
    add_code(doc, "text", "focal_length_px = frame_width_px / (2 × tan(HORIZONTAL_FOV_DEG / 2))\n\n车辆：\ndistance_m = focal_length_px × VEHICLE_WIDTHS_M[class_id] / box_width_px\n\n人物：\ndistance_by_width  = focal_length_px × 0.8 / box_width_px\ndistance_by_height = focal_length_px × 1.7 / box_height_px\ndistance_m = min(distance_by_width, distance_by_height)")
    add_para(doc, "车辆类别先验宽度来自 VEHICLE_WIDTHS_M：bus 2.5 m、car 1.8 m、microbus 2.0 m、motorbike 0.8 m、pickup-van 2.0 m、truck 2.5 m；人物使用约 0.8 m 宽度和 1.7 m 高度。它们是工程初始估计，不是每辆车或每个人的真实尺寸。")
    add_callout(doc, "⚠️ 注意", "单目测距对检测框边缘、遮挡、俯仰角、镜头畸变、车辆类别误判和真实目标尺寸高度敏感。安全距离是风险策略阈值，不等于经过标定的绝对物理距离。", "FFF2CC")
    section(doc, "6.4 接近速度")
    add_para(doc, "当轨迹存在上一帧距离和时间时，代码按 speed=(previous_distance-distance)/delta_time 计算接近速度。距离变小得到正速度，距离变大得到负速度。车辆在 10～25 m 区间只有当首次测距或速度达到 ATTENTION_SPEED_MPS=0.2 m/s 时进入注意候选；人物主要按距离阈值判断。")
    section(doc, "6.5 风险等级与连续确认")
    add_table(doc, ["风险", "车辆规则", "人物规则", "输出"], [
        ("0 安全", "距离>25 m，或未满足接近条件", "距离>40 m", "绿色 OSD，无提示音"),
        ("1 注意", "10～25 m 且正在接近", "15～40 m", "注意颜色和低频提示"),
        ("2 危险", "距离≤10 m", "距离≤15 m", "危险颜色、语音和蜂鸣器"),
    ], [2.2, 5.1, 4.0, 3.2])
    add_para(doc, "风险不会在第一次出现时立即确认。相同候选风险连续出现至少 RISK_CONFIRM_FRAMES=2 帧后，track['risk'] 才变为 1 或 2。风险回到 0 时候选帧计数清零。程序启动后的 STARTUP_GRACE_MS=1200 ms 内会强制 overall_risk 和 alert_risk 为 0。")
    section(doc, "6.6 报警优先级")
    add_para(doc, "车辆和人物分别统计 person_alert、vehicle_alert。人物报警优先级更高：当人物存在已确认风险时选择人物语音，否则使用车辆语音。报警更新由非阻塞 AlertController 执行，UART STOP 时调用 alert.update(0, False, 0) 关闭输出。")
    section(doc, "6.7 参数调优建议")
    add_bullets(doc, [
        "误检多：逐步提高类别最低置信度或全局置信度，检查是否由反光、车灯、树影造成。",
        "远距离漏检：优先验证 640 车辆模型或增加同场景训练数据，不要只盲目降低阈值。",
        "框抖动：提高或降低 TRACK_IOU_THRESHOLD 需要结合目标速度和帧率验证；同时检查检测框是否稳定。",
        "报警过早：重新标定 FOV、车辆宽度/人物高度和安全距离，不能只修改声音冷却时间。",
        "启动误报：调整 STARTUP_GRACE_MS 或摄像头/音频初始化顺序，保持连续帧确认。",
    ])

    chapter(doc, "第 7 章 测试与验证")
    section(doc, "7.1 模型验证数据")
    add_table(doc, ["指标", "320 车辆", "640 车辆"], [
        ("Precision", "0.7707", "0.8148"), ("Recall", "0.7056", "0.7613"),
        ("mAP50", "0.7580", "0.8168"), ("mAP50-95", "0.4416", "0.4928"),
        ("bus mAP50-95", "0.546", "0.592"), ("car mAP50-95", "0.491", "0.528"),
        ("microbus mAP50-95", "0.414", "0.475"), ("motorbike mAP50-95", "0.337", "0.389"),
        ("pickup-van mAP50-95", "0.483", "0.540"), ("truck mAP50-95", "0.379", "0.433"),
    ], [5.0, 4.0, 4.0])
    add_para(doc, "指标来自 1046 张验证图片和 6014 个实例。640 精度更高，但它当前只用于车辆检测；320 是自动启动双模型的默认实时方案。")
    section(doc, "7.2 板端验证矩阵")
    add_table(doc, ["测试项", "步骤", "通过判据", "当前证据"], [
        ("摄像头", "启动预览或主程序", "GC2093 图像稳定，无初始化异常", "board_test.md"),
        ("320 车辆", "加载 best_320.kmodel 连续运行", "KPU 约 29 ms，检测输出稳定", "board_test.md"),
        ("人物模型", "加载 person_320.kmodel", "PERSON 计数可输出，双模型可运行", "board_test.md"),
        ("640 车辆", "加载报告中的 640 模型", "约 9.1 FPS，KPU 约 98 ms", "历史报告；当前目录需补齐产物"),
        ("虚拟显示", "DISPLAY_MODE=virt", "800×480 原图和 ARGB OSD 正常", "board_test.md"),
        ("LCD", "DISPLAY_MODE=lcd", "LCD 有实时画面和 OSD", "board_test.md"),
        ("蜂鸣器", "触发人物/车辆风险", "YbBuzzer 非阻塞触发", "源码与历史实测记录"),
        ("语音", "检查 PCM 并触发提示", "人物/车辆使用不同 PCM", "源码和 PCM 文件"),
        ("UART", "发送 01/00", "返回 START/STOP，STOP 时静音", "serial_control.py"),
        ("自动启动", "软重启或重新上电", "main.py 加载应用并输出 STATS", "board_test.md"),
    ], [2.8, 4.6, 5.3, 3.2])
    section(doc, "7.3 测试用例")
    add_table(doc, ["编号", "场景", "预期结果"], [
        ("TC-01", "无目标背景", "SAFE、无框、无语音和蜂鸣"),
        ("TC-02", "单辆车远距离静止", "车辆类别和距离显示，风险为安全"),
        ("TC-03", "车辆从远处接近", "连续 2 帧确认后进入注意或危险"),
        ("TC-04", "人物进入画面", "PERSON 计数增加，使用人物阈值和人物提示音"),
        ("TC-05", "目标短暂闪现一帧", "不应立即触发确认后的报警"),
        ("TC-06", "启动后立即出现目标", "前 1.2 秒不报警"),
        ("TC-07", "UART 发送 00", "停止取帧/推理/报警并返回 STOP"),
        ("TC-08", "UART 发送 01", "恢复运行并返回 START"),
        ("TC-09", "中文路径转换", "转换失败时改用 C:\\k230_deploy"),
        ("TC-10", "模型文件缺失", "记录错误或退化到车辆模式，不得静默假装双模型"),
    ], [2.0, 6.0, 8.0])
    section(doc, "7.4 FAQ")
    add_para(doc, "Q：为什么 IDE 画面黑？\nA：确认使用当前双层显示实现：视频层输出 YUV 原图，ARGB OSD 叠加检测结果；不要把 RGB565 快照直接当作虚拟显示最终路径。")
    add_para(doc, "Q：为什么人物模型没有显示？\nA：检查 /sdcard/rear_vehicle/person_320.kmodel 是否存在、是否成功加载，以及测试画面是否真的有人物。日志中的 PERSON=0 只说明当前画面没有通过过滤的人物，不等于模型没有加载。")
    add_para(doc, "Q：为什么 640 命令不能直接执行？\nA：当前正式工作树缺少 best_640.onnx、best_640.kmodel 等文件。先恢复并校验历史产物，再执行 640 流程。")
    add_para(doc, "Q：为什么距离不准？\nA：默认 FOV、车辆宽度、人物高度只是初始先验。应在实际镜头安装位置下用多个真实距离点重新拟合。")
    add_para(doc, "Q：STOP 是否退出程序？\nA：不会。STOP 只暂停取帧、推理和报警，模型保持加载，后续发送 START 可恢复。")

    chapter(doc, "第 8 章 性能与资源分析")
    section(doc, "8.1 实测条件")
    add_para(doc, "性能数据来自 CanMV K230 YAHBOOM 1G、GC2093 CSI2、CanMV IDE 固件 0.4.0 的板端记录。默认输入为 320×320 RGB888P，虚拟显示为 800×480；部分记录还包含 ST7701 LCD。以下数据必须结合“是否包含人物模型、显示、报警和统计窗口”理解，不能横向套用到其他 K230 板卡。")
    add_table(doc, ["配置", "模型", "输入", "人物模型", "实测数据", "显示/报警口径"], [
        ("320 车辆阶段", "best_320.kmodel", "320×320", "否", "KPU 约 29 ms；后处理约 0.9 ms；纯车辆约 18～20 FPS", "报告中的车辆阶段"),
        ("320 双模型", "best_320 + person_320", "320×320", "是", "总帧率约 12.8 FPS", "包含双模型循环；显示和报警随运行版本变化"),
        ("640 车辆", "best_640.kmodel", "640×640", "否", "KPU 约 98 ms；后处理约 2.7 ms；约 9.1 FPS", "车辆单模型报告"),
        ("IDE 显示", "显示链路", "800×480", "不适用", "显示刷新约 28.6 FPS", "是显示刷新统计，不等于 AI FPS"),
        ("LCD 运行", "320 双模型版本", "320×320", "是", "报告记录约 13.8 FPS", "包含 LCD 运行环境"),
    ], [2.3, 3.8, 2.0, 2.2, 6.0, 4.6])
    add_callout(doc, "⚠️ 注意", "board_test.md 的典型日志窗口出现过 13.68～13.75 FPS，而同一报告的平均口径给出 320 车辆纯模型约 18～20 FPS；这是不同运行配置、显示/统计窗口或版本记录的差异。正式报告应同时保留原始日志和测试条件，不能将所有数字拼成一个无条件的 FPS。", "FFF2CC")
    section(doc, "8.2 后处理优化")
    add_para(doc, "初版 Python 后处理曾约 117 ms，导致帧率约 5 FPS。当前版本使用 ulab.numpy 的 max、argmax、nonzero 先进行向量化置信度和类别筛选，只对少量候选执行 Python NMS，使车辆后处理约降至 0.9 ms；640 后处理约 2.7 ms。")
    section(doc, "8.3 显示与报警开销")
    add_para(doc, "STATS 日志分别统计 cap、detect、risk、draw 和 show。虚拟显示采用视频层+ARGB OSD，摄像头原图不需要每帧由 Python 拷贝到 OSD。语音使用后台线程，蜂鸣器使用非阻塞控制，目标是避免报警播放阻塞 AI 循环。显示刷新率和 AI 推理 FPS 是两个指标，必须分开报告。")
    section(doc, "8.4 内存、功耗与限制")
    add_para(doc, "当前工程报告没有给出经过统一仪器、统一负载和统一显示模式测量的内存峰值与功耗曲线，因此本文不填入虚构数值。模型大小、双模型同时驻留、PCM 缓冲、OSD 图层和 Python 堆都会影响资源使用。正式产品化前应增加启动峰值、稳定运行、显示开启/关闭、报警开启/关闭四组测量。")
    add_bullets(doc, [
        "小目标：320 输入会损失远距离和小目标像素信息，640 可改善部分召回但速度下降。",
        "夜间：车灯、噪声、曝光和反光可能造成漏检或误检。",
        "遮挡：IoU 跟踪依赖检测框连续重叠，长时间遮挡会产生新轨迹。",
        "反光：车窗、尾灯、金属反光可能触发类别过滤前的候选框。",
        "测距：实际宽度、视场角和安装姿态误差会直接传递到风险等级。",
    ])

    chapter(doc, "第 9 章 C++ RTOS 方案现状与后续规划")
    section(doc, "9.1 当前状态")
    add_para(doc, "当前交付是 CanMV MicroPython 方案，板端使用 AIBase、Ai2d、PipeLine、nncase_runtime、media、YbSpeaker、YbBuzzer 和 machine UART。工程没有已完成的 C++ RTOS 生产应用，也没有可声称已验证的 yolov5.cc、yolov5.h、ai_base C++ 应用或 pipeline C++ 应用。")
    section(doc, "9.2 MicroPython 方案边界")
    add_bullets(doc, [
        "优点：迭代快，便于验证摄像头、KMODEL、显示、音频和串口链路。",
        "边界：Python 后处理、线程、垃圾回收、异常恢复和资源生命周期需要谨慎控制。",
        "边界：当前测距仍是启发式单目估计，未达到经过实车标定的安全系统等级。",
        "边界：没有完整生产固件镜像、OTA、日志持久化、看门狗策略和量产测试流程。",
    ])
    section(doc, "9.3 未来 C++ 迁移模块")
    add_numbered(doc, [
        "封装 Sensor/媒体管线和双通道视频输入。",
        "封装 AI2D 和 KPU KMODEL 生命周期，明确输入输出张量所有权。",
        "将 YOLO 输出解析、类别过滤、NMS 和轨迹管理改成固定内存策略。",
        "将测距、风险状态机、连续帧确认和报警冷却实现为可测试模块。",
        "实现显示 OSD、PCM 播放、YbBuzzer 和 UART1 的异步任务。",
        "增加看门狗、异常重启、配置版本和现场日志。",
    ])
    add_callout(doc, "📌 设计决策说明", "C++ RTOS 是后续生产化方向，不应为了满足“完整方案”而把规划代码、参考 SDK 或源码片段写成当前已完成交付。", "DDEBF7")

    chapter(doc, "第 10 章 总结与扩展")
    section(doc, "10.1 已完成内容")
    add_bullets(doc, [
        "车辆 YOLO11n 六类模型已完成 best.pt、320 ONNX 和 320 KMODEL 部署链路。",
        "COCO YOLO11n person 独立模型已生成 person_320.onnx/person_320.kmodel，并接入 320 双模型板端程序。",
        "板端完成摄像头采集、AI2D、KPU 推理、后处理、NMS、IoU 跟踪、测距、风险判断和 OSD。",
        "完成 CanMV IDE 虚拟显示、LCD/HDMI 兼容路径、开机自动启动和 UART1 启停控制。",
        "完成 YbSpeaker PCM 语音和 YbBuzzer 非阻塞报警链路。",
        "已获得 320/640 车辆模型对比指标以及 320 双模型约 12.8 FPS 的实测记录。",
    ])
    section(doc, "10.2 尚未完成内容")
    add_bullets(doc, [
        "当前工作树没有完整、可直接复现的 640 ONNX/KMODEL/板端程序正式文件，需要整理和校验。",
        "测距、FOV、目标宽度和报警阈值仍需真实车辆和实际安装位置标定。",
        "没有完整的 K230 固件镜像、C++ RTOS 生产应用、量产测试和 OTA 方案。",
        "没有已验证的 test_capture.py 和 X-AnyLabeling 标注闭环。",
        "没有统一条件下的内存峰值、功耗和长期稳定性测试报告。",
    ])
    section(doc, "10.3 扩展路线")
    add_numbered(doc, [
        "补齐并校验 640 模型产物，建立模型、转换参数和 SHA256 清单。",
        "建立实际相机安装条件下的多距离标定表，并根据车型分别拟合宽度先验。",
        "增加车道线或感兴趣区域过滤，降低非行驶区域目标对报警的影响。",
        "升级到更稳定的多目标跟踪算法，处理遮挡、交叉和短时漏检。",
        "增加 RTSP 推流或远程状态接口，但必须评估带宽和双模型性能损失。",
        "按模块迁移到 C++/RTOS，增加看门狗、故障恢复、功耗管理和量产测试。",
    ])
    add_callout(doc, "📌 最终结论", "当前工程已经形成一条可在 CanMV K230 YAHBOOM 1G 上运行的 YOLO11n 车辆+人物 MicroPython 双模型预警链路。320 版本是当前实时预警默认方案；640 版本在报告中表现出更高车辆检测指标，但当前正式工作树的产物完整性仍需补齐。系统输出的是基于单目估计的接近风险，正式上车或量产前必须完成实车标定、长期稳定性测试和安全策略复核。", "DDEBF7")

    doc.add_heading("附录 A：关键源文件索引", level=1)
    add_table(doc, ["文件", "用途"], [
        ("k230_deploy/board/rear_vehicle_yolo11.py", "当前板端主程序、DetectionApp、双模型、跟踪、风险和报警"),
        ("k230_deploy/board/main.py", "MicroPython 开机自动启动入口"),
        ("k230_deploy/board/serial_control.py", "UART1 启停协议"),
        ("k230_deploy/tools/export_onnx.py", "车辆模型固定输入 ONNX 导出"),
        ("k230_deploy/tools/convert_kmodel.py", "nncase KMODEL 转换和 PTQ 校准"),
        ("k230_deploy/config/dataset.yaml", "车辆六类数据集配置"),
        ("k230_deploy/config/gpu_train_args.yaml", "YOLO11n GPU 训练参数"),
        ("k230_deploy/reports/board_test.md", "K230 实机验证日志和性能数据"),
        ("k230_deploy/reports/comparison.md", "320/640 车辆模型精度和性能对比"),
        ("k230_deploy/reports/solution_status.md", "工程状态清单"),
    ], [7.5, 8.0])
    add_callout(doc, "⚠️ 版本差异记录", "board_test.md 中的部分段落记录的是较早蜂鸣器开关或频率状态；当前源码使用 ENABLE_PERSON_SPEAKER/ENABLE_VEHICLE_SPEAKER，并以当前 board 文件为准。reports/manifest.json 中的 640 文件记录也不能替代当前正式目录中的实际文件。", "FFF2CC")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    write_doc()
