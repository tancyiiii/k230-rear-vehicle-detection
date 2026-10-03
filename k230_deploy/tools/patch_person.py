from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")

text = text.replace(
    'MODEL_INPUT_SIZE = 320\n',
    'MODEL_INPUT_SIZE = 320\nPERSON_KMODEL_PATH = "/sdcard/rear_vehicle/person_320.kmodel"\nPERSON_CLASS_ID = 6\n',
    1,
)
text = text.replace(
    'LABELS = ["bus", "car", "microbus", "motorbike", "pickup-van", "truck"]\nVEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5]\n',
    'LABELS = ["bus", "car", "microbus", "motorbike", "pickup-van", "truck", "person"]\nVEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5, 0.5]\nVEHICLE_CLASS_MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}\nPERSON_CLASS_MAP = {0: PERSON_CLASS_ID}\n',
    1,
)
text = text.replace(
    '        display_size,\n        debug_mode=0,\n    ):\n',
    '        display_size,\n        class_map,\n        debug_mode=0,\n    ):\n',
    1,
)
text = text.replace(
    '        self.debug_mode = debug_mode\n        self.x_factor',
    '        self.debug_mode = debug_mode\n        self.class_map = class_map\n        self.x_factor',
    1,
)
text = text.replace(
    '            (255, 0, 60, 100),\n        ]',
    '            (255, 0, 60, 100),\n            (255, 255, 255, 255),\n        ]',
    1,
)
text = text.replace(
    '            best_score = float(best_scores[index])\n            best_class = int(best_classes[index])\n',
    '            best_score = float(best_scores[index])\n            model_class = int(best_classes[index])\n            best_class = self.class_map.get(model_class)\n            if best_class is None:\n                continue\n',
    1,
)

text = text.replace(
    '    detector = None\n    alert = None\n',
    '    vehicle_detector = None\n    person_detector = None\n    alert = None\n',
    1,
)
text = text.replace(
    '        detector = DetectionApp(\n            KMODEL_PATH,\n            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),\n            rgb888p_size=RGB888P_SIZE,\n            display_size=DISPLAY_SIZE,\n            debug_mode=0,\n        )\n        detector.config_preprocess()\n        print("rear vehicle ready:", KMODEL_PATH, "display:", DISPLAY_MODE)\n',
    '        vehicle_detector = DetectionApp(\n            KMODEL_PATH,\n            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),\n            rgb888p_size=RGB888P_SIZE,\n            display_size=DISPLAY_SIZE,\n            class_map=VEHICLE_CLASS_MAP,\n            debug_mode=0,\n        )\n        vehicle_detector.config_preprocess()\n        person_detector = DetectionApp(\n            PERSON_KMODEL_PATH,\n            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),\n            rgb888p_size=RGB888P_SIZE,\n            display_size=DISPLAY_SIZE,\n            class_map=PERSON_CLASS_MAP,\n            debug_mode=0,\n        )\n        person_detector.config_preprocess()\n        print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "display:", DISPLAY_MODE)\n',
    1,
)
text = text.replace(
    '                tensors = detector.preprocess(frame)\n                pre_end = time.ticks_ms()\n                results = detector.inference(tensors)\n                kpu_end = time.ticks_ms()\n                detections = detector.postprocess(results)\n                infer_end = time.ticks_ms()\n',
    '                vehicle_tensors = vehicle_detector.preprocess(frame)\n                vehicle_results = vehicle_detector.inference(vehicle_tensors)\n                vehicle_detections = vehicle_detector.postprocess(vehicle_results)\n                pre_end = time.ticks_ms()\n                person_tensors = person_detector.preprocess(frame)\n                person_results = person_detector.inference(person_tensors)\n                person_detections = person_detector.postprocess(person_results)\n                detections = vehicle_detections + person_detections\n                kpu_end = time.ticks_ms()\n                infer_end = kpu_end\n',
    1,
)
text = text.replace(
    '                detector.draw_result(pipeline, draw_detections, overall_risk)\n',
    '                vehicle_detector.draw_result(pipeline, draw_detections, overall_risk)\n',
    1,
)
text = text.replace(
    '        if detector is not None:\n            detector.deinit()\n',
    '        if person_detector is not None:\n            person_detector.deinit()\n        if vehicle_detector is not None:\n            vehicle_detector.deinit()\n',
    1,
)

path.write_text(text, encoding="utf-8")
print("patched", path)
