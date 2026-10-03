from pathlib import Path

for name in ("rear_vehicle_yolo11.py", "rear_vehicle_yolo11_640.py"):
    path = Path(r"C:\k230_deploy\board") / name
    text = path.read_text(encoding="utf-8")
    text = text.replace("MODEL_INPUT_SIZE=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)", "model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)")
    text = text.replace("        print(\"rear vehicle error:\", error)\n        sys.print_exception(error)", "        print(\"rear vehicle error:\", error)")
    path.write_text(text, encoding="utf-8")
    print("patched", path)
