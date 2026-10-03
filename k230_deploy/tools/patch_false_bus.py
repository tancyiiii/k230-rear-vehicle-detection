from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text=p.read_text(encoding="utf-8")
text=text.replace(
    "MAX_BOXES = 50\n",
    "MAX_BOXES = 50\nCLASS_MIN_CONFIDENCE = {0: 0.65, 1: 0.45, 2: 0.50, 3: 0.45, 4: 0.60, 5: 0.65, 6: 0.20}\nMAX_BUS_AREA_RATIO = 0.55\nWHOLE_FRAME_AREA_RATIO = 0.88\n",
    1,
)
text=text.replace(
    "            if right - left < 4 or bottom - top < 4:\n                continue\n\n            boxes.append([left, top, right, bottom])\n",
    "            box_width = right - left\n            box_height = bottom - top\n            if box_width < 4 or box_height < 4:\n                continue\n\n            area_ratio = float(box_width * box_height) / float(\n                self.rgb888p_size[0] * self.rgb888p_size[1]\n            )\n            min_confidence = CLASS_MIN_CONFIDENCE.get(best_class, CONFIDENCE_THRESHOLD)\n            if best_score < min_confidence:\n                continue\n            if area_ratio > WHOLE_FRAME_AREA_RATIO:\n                continue\n            if best_class == 0 and area_ratio > MAX_BUS_AREA_RATIO and best_score < 0.90:\n                continue\n            if best_class in (4, 5) and area_ratio > 0.72 and best_score < 0.90:\n                continue\n\n            boxes.append([left, top, right, bottom])\n",
    1,
)
text=text.replace(
    'detail_parts.append("{}:{:.2f}/{:.1f}m/R{}".format(\n                            LABELS[track["class_id"]],\n                            track["score"],\n                            track["distance_m"],\n                            track["risk"],\n                        ))',
    'detail_parts.append("{}:{:.2f}/{:.1f}m/W{}%/H{}%/R{}".format(\n                            LABELS[track["class_id"]],\n                            track["score"],\n                            track["distance_m"],\n                            int((track["bbox"][2] - track["bbox"][0]) * 100 / RGB888P_SIZE[0]),\n                            int((track["bbox"][3] - track["bbox"][1]) * 100 / RGB888P_SIZE[1]),\n                            track["risk"],\n                        ))',
    1,
)
p.write_text(text,encoding="utf-8")
print("patched",p)
