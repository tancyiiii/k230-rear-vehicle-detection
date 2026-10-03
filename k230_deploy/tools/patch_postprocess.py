from pathlib import Path

old = '''        boxes = []
        scores = []
        class_ids = []
        rows = output.shape[0]
        channels = output.shape[1]

        for index in range(rows):
            best_score = 0.0
            best_class = 0
            for class_id in range(4, channels):
                score = float(output[index, class_id])
                if score > best_score:
                    best_score = score
                    best_class = class_id - 4
            if best_score < CONFIDENCE_THRESHOLD:
                continue

            cx = float(output[index, 0])
            cy = float(output[index, 1])
            width = float(output[index, 2])
            height = float(output[index, 3])
'''
new = '''        boxes_data = output[:, 0:4]
        scores_data = output[:, 4:]
        best_scores = np.max(scores_data, axis=1)
        best_classes = np.argmax(scores_data, axis=1)
        selected = np.nonzero(best_scores >= CONFIDENCE_THRESHOLD)[0]

        boxes = []
        scores = []
        class_ids = []
        for selected_index in selected:
            index = int(selected_index)
            best_score = float(best_scores[index])
            best_class = int(best_classes[index])

            cx = float(boxes_data[index, 0])
            cy = float(boxes_data[index, 1])
            width = float(boxes_data[index, 2])
            height = float(boxes_data[index, 3])
'''
for name in ("rear_vehicle_yolo11.py", "rear_vehicle_yolo11_640.py"):
    path = Path(r"C:\k230_deploy\board") / name
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"postprocess block not found: {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("patched", path)
