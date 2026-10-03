# -*- coding: utf-8 -*-
"""K230 rear-vehicle recognition with YOLO11 and buzzer alerts.

Deploy layout on the K230 SD card:
    /sdcard/rear_vehicle/best_320.kmodel
    /sdcard/rear_vehicle/rear_vehicle_yolo11.py

This script follows the official CanMV K230 PipeLine/AIBase/Ai2d workflow.
"""

import gc
import math
import os
import sys
import time

import image
import nncase_runtime as nn
import ulab.numpy as np
from libs.AI2D import Ai2d
from libs.AIBase import AIBase
from libs.PipeLine import PipeLine, ScopedTiming
from media.display import *
from media.media import *
from media.sensor import *

try:
    from ybUtils.YbBuzzer import YbBuzzer
except BaseException:
    YbBuzzer = None


# ---------------------------- deployment settings ----------------------------
KMODEL_PATH = "/sdcard/rear_vehicle/best_320.kmodel"
MODEL_INPUT_SIZE = 320
PERSON_KMODEL_PATH = "/sdcard/rear_vehicle/person_320.kmodel"
PERSON_CLASS_ID = 6
RGB888P_SIZE = [320, 320]
DISPLAY_SIZE = [800, 480]
DISPLAY_MODE = "virt"  # "virt" for CanMV IDE, "lcd" physical screen, "hdmi"

LABELS = ["bus", "car", "microbus", "motorbike", "pickup-van", "truck", "person"]
VEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5, 0.8]
VEHICLE_CLASS_MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
PERSON_CLASS_MAP = {0: PERSON_CLASS_ID}

CONFIDENCE_THRESHOLD = 0.40
NMS_THRESHOLD = 0.40
MAX_BOXES = 50
CLASS_MIN_CONFIDENCE = {0: 0.65, 1: 0.45, 2: 0.50, 3: 0.45, 4: 0.60, 5: 0.65, 6: 0.20}
MAX_BUS_AREA_RATIO = 0.55
WHOLE_FRAME_AREA_RATIO = 0.88

HORIZONTAL_FOV_DEG = 120.0
SAFE_DISTANCE_M = 25.0
DANGER_DISTANCE_M = 10.0
ATTENTION_SPEED_MPS = 0.2
PERSON_SAFE_DISTANCE_M = 40.0
PERSON_DANGER_DISTANCE_M = 15.0
PERSON_HEIGHT_M = 1.7
RISK_CONFIRM_FRAMES = 2
STARTUP_GRACE_MS = 1200

ENABLE_PERSON_BUZZER = True
ENABLE_VEHICLE_BUZZER = False
BUZZER_DUTY = 50
TRACK_IOU_THRESHOLD = 0.30
TRACK_MAX_AGE_MS = 1200
DEBUG_LOG_EVERY_FRAMES = 30

COLOR_SAFE = (255, 40, 210, 80)
COLOR_ATTENTION = (255, 255, 210, 30)
COLOR_DANGER = (255, 255, 40, 40)
COLOR_TEXT = (255, 255, 255, 255)


def _clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def _box_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    intersection = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union


class VirtualPipeLine:
    """Official K230 layer pipeline using the CanMV IDE virtual frame buffer.

    chn0 输出 YUV 并 bind_layer 到显示视频层（摄像头原图直通），
    chn2 输出 RGB888P 供 AI 推理，OSD 用独立 ARGB8888 图层叠加检测框。
    """

    def __init__(self, rgb888p_size, display_size):
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        self.sensor = None
        self.osd_img = None
        self.ready = False

    def create(self):
        self.sensor = Sensor(id=2)
        self.sensor.reset()
        self.sensor.set_framesize(width=self.display_size[0], height=self.display_size[1], chn=CAM_CHN_ID_0)
        self.sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420, chn=CAM_CHN_ID_0)
        self.sensor.set_framesize(width=self.rgb888p_size[0], height=self.rgb888p_size[1], chn=CAM_CHN_ID_2)
        self.sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)
        self.osd_img = image.Image(self.display_size[0], self.display_size[1], image.ARGB8888)
        bind_info = self.sensor.bind_info(x=0, y=0, chn=CAM_CHN_ID_0)
        Display.bind_layer(**bind_info, layer=Display.LAYER_VIDEO1)
        Display.init(Display.VIRT, width=self.display_size[0], height=self.display_size[1], to_ide=True)
        MediaManager.init()
        self.sensor.run()
        self.ready = True

    def get_frame(self):
        ai_frame = self.sensor.snapshot(chn=CAM_CHN_ID_2)
        return ai_frame.to_numpy_ref()

    def show_image(self):
        Display.show_image(self.osd_img, 0, 0, Display.LAYER_OSD3)

    def destroy(self):
        if self.sensor is not None:
            try:
                self.sensor.stop()
            except BaseException:
                pass
        try:
            Display.deinit()
        except BaseException:
            pass
        try:
            MediaManager.deinit()
        except BaseException:
            pass


class DetectionApp(AIBase):
    def __init__(
        self,
        kmodel_path,
        model_input_size,
        rgb888p_size,
        display_size,
        class_map,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        target_class_index=None,
        debug_mode=0,
    ):
        super().__init__(
            kmodel_path,
            model_input_size=model_input_size,
            rgb888p_size=rgb888p_size,
            debug_mode=debug_mode,
        )
        self.model_input_size = model_input_size
        self.rgb888p_size = rgb888p_size
        self.display_size = display_size
        self.debug_mode = debug_mode
        self.class_map = class_map
        self.confidence_threshold = confidence_threshold
        self.target_class_index = target_class_index
        self.x_factor = float(rgb888p_size[0]) / float(model_input_size[0])
        self.y_factor = float(rgb888p_size[1]) / float(model_input_size[1])
        self.colors = [
            (255, 220, 20, 60),
            (255, 119, 11, 32),
            (255, 0, 0, 142),
            (255, 0, 0, 230),
            (255, 106, 0, 228),
            (255, 0, 60, 100),
            (255, 255, 255, 255),
        ]
        self.ai2d = Ai2d(debug_mode)
        self.ai2d.set_ai2d_dtype(
            nn.ai2d_format.NCHW_FMT,
            nn.ai2d_format.NCHW_FMT,
            np.uint8,
            np.uint8,
        )

    def config_preprocess(self):
        self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
        self.ai2d.build(
            [1, 3, self.rgb888p_size[1], self.rgb888p_size[0]],
            [1, 3, self.model_input_size[1], self.model_input_size[0]],
        )

    def postprocess(self, results):
        if not results:
            return []

        output = results[0]
        if len(output.shape) == 3:
            output = output[0]
        if len(output.shape) != 2:
            return []

        # YOLO output may be (4 + classes, anchors) or (anchors, 4 + classes).
        if output.shape[0] < output.shape[1]:
            output = output.transpose()

        boxes_data = output[:, 0:4]
        scores_data = output[:, 4:]
        if self.target_class_index is None:
            best_scores = np.max(scores_data, axis=1)
            best_classes = np.argmax(scores_data, axis=1)
        else:
            index = self.target_class_index
            best_scores = np.max(scores_data[:, index:index + 1], axis=1)
            best_classes = None
        selected = np.nonzero(best_scores >= self.confidence_threshold)[0]

        boxes = []
        scores = []
        class_ids = []
        for selected_index in selected:
            index = int(selected_index)
            best_score = float(best_scores[index])
            if self.target_class_index is None:
                model_class = int(best_classes[index])
            else:
                model_class = self.target_class_index
            best_class = self.class_map.get(model_class)
            if best_class is None:
                continue

            cx = float(boxes_data[index, 0])
            cy = float(boxes_data[index, 1])
            width = float(boxes_data[index, 2])
            height = float(boxes_data[index, 3])
            left = int((cx - 0.5 * width) * self.x_factor)
            top = int((cy - 0.5 * height) * self.y_factor)
            right = int((cx + 0.5 * width) * self.x_factor)
            bottom = int((cy + 0.5 * height) * self.y_factor)

            left = _clamp(left, 0, self.rgb888p_size[0] - 1)
            top = _clamp(top, 0, self.rgb888p_size[1] - 1)
            right = _clamp(right, left + 1, self.rgb888p_size[0])
            bottom = _clamp(bottom, top + 1, self.rgb888p_size[1])
            box_width = right - left
            box_height = bottom - top
            if box_width < 4 or box_height < 4:
                continue

            area_ratio = float(box_width * box_height) / float(
                self.rgb888p_size[0] * self.rgb888p_size[1]
            )
            min_confidence = CLASS_MIN_CONFIDENCE.get(best_class, CONFIDENCE_THRESHOLD)
            if best_score < min_confidence:
                continue
            if area_ratio > WHOLE_FRAME_AREA_RATIO:
                continue
            if best_class == 0 and area_ratio > MAX_BUS_AREA_RATIO and best_score < 0.90:
                continue
            if best_class in (4, 5) and area_ratio > 0.72 and best_score < 0.90:
                continue

            boxes.append([left, top, right, bottom])
            scores.append(best_score)
            class_ids.append(best_class)

        keep = self._nms(boxes, scores)
        result = []
        for index in keep[:MAX_BOXES]:
            result.append(
                boxes[index]
                + [scores[index], class_ids[index]]
            )
        return result

    def _nms(self, boxes, scores):
        if not boxes:
            return []
        order = list(range(len(scores)))
        order.sort(key=lambda item: scores[item], reverse=True)
        keep = []
        while order:
            current = order[0]
            order = order[1:]
            keep.append(current)
            remaining = []
            for candidate in order:
                if _box_iou(boxes[current], boxes[candidate]) < NMS_THRESHOLD:
                    remaining.append(candidate)
            order = remaining
        return keep

    def draw_result(self, pipeline, detections, overall_risk):
        # OSD 是独立 ARGB 图层；clear 只清检测框，摄像头画面由视频层直通，不受影响。
        pipeline.osd_img.clear()
        for detection in detections:
            x1, y1, x2, y2 = detection[:4]
            class_id = int(detection[5])
            score = float(detection[4])
            distance = float(detection[6])
            risk = int(detection[7])
            color = self.colors[class_id % len(self.colors)]
            if risk == 2:
                color = COLOR_DANGER
            elif risk == 1:
                color = COLOR_ATTENTION

            x = x1 * self.display_size[0] // self.rgb888p_size[0]
            y = y1 * self.display_size[1] // self.rgb888p_size[1]
            width = (x2 - x1) * self.display_size[0] // self.rgb888p_size[0]
            height = (y2 - y1) * self.display_size[1] // self.rgb888p_size[1]
            pipeline.osd_img.draw_rectangle(
                x,
                y,
                width,
                height,
                color=color,
                thickness=4,
            )
            text = "{} {:.2f} {:.1f}m".format(
                LABELS[class_id],
                score,
                distance,
            )
            pipeline.osd_img.draw_string_advanced(
                _clamp(x, 0, self.display_size[0] - 180),
                _clamp(y - 40, 0, self.display_size[1] - 32),
                28,
                text,
                color=COLOR_TEXT,
            )

        status = "SAFE"
        status_color = COLOR_SAFE
        if overall_risk == 1:
            status = "ATTENTION"
            status_color = COLOR_ATTENTION
        elif overall_risk == 2:
            status = "DANGER"
            status_color = COLOR_DANGER
        pipeline.osd_img.draw_string_advanced(
            12,
            12,
            36,
            "REAR: " + status,
            color=status_color,
        )


class SimpleTracker:
    def __init__(self):
        self.tracks = []
        self.next_id = 1

    def update(self, detections, now_ms):
        for track in self.tracks:
            track["matched"] = False

        unmatched = []
        for detection in detections:
            best_track = None
            best_iou = 0.0
            for track in self.tracks:
                if track["matched"] or track["class_id"] != int(detection[5]):
                    continue
                iou = _box_iou(track["bbox"], detection[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_track = track
            if best_track is not None and best_iou >= TRACK_IOU_THRESHOLD:
                best_track["bbox"] = detection[:4]
                best_track["score"] = float(detection[4])
                best_track["last_seen_ms"] = now_ms
                best_track["matched"] = True
            else:
                unmatched.append(detection)

        for detection in unmatched:
            track = {
                "id": self.next_id,
                "bbox": detection[:4],
                "score": float(detection[4]),
                "class_id": int(detection[5]),
                "last_seen_ms": now_ms,
                "matched": True,
                "previous_distance_m": None,
                "previous_time_ms": None,
                "distance_m": 0.0,
                "speed_mps": 0.0,
                "candidate_risk": 0,
                "risk_frames": 0,
                "risk": 0,
            }
            self.next_id += 1
            self.tracks.append(track)

        self.tracks = [
            track
            for track in self.tracks
            if time.ticks_diff(now_ms, track["last_seen_ms"]) <= TRACK_MAX_AGE_MS
        ]
        return self.tracks


class RiskController:
    def __init__(self, frame_width_px):
        half_fov = math.radians(HORIZONTAL_FOV_DEG * 0.5)
        self.focal_length_px = float(frame_width_px) / (2.0 * math.tan(half_fov))

    def evaluate(self, tracks, now_ms):
        overall = 0
        results = []
        for track in tracks:
            if not track["matched"]:
                continue
            x1, y1, x2, y2 = track["bbox"]
            width_px = max(1.0, float(x2 - x1))
            height_px = max(1.0, float(y2 - y1))
            class_id = _clamp(int(track["class_id"]), 0, len(VEHICLE_WIDTHS_M) - 1)
            if class_id == PERSON_CLASS_ID:
                distance_by_width = self.focal_length_px * VEHICLE_WIDTHS_M[class_id] / width_px
                distance_by_height = self.focal_length_px * PERSON_HEIGHT_M / height_px
                distance = min(distance_by_width, distance_by_height)
            else:
                distance = self.focal_length_px * VEHICLE_WIDTHS_M[class_id] / width_px

            previous_distance = track["previous_distance_m"]
            previous_time = track["previous_time_ms"]
            speed = 0.0
            if previous_distance is not None and previous_time is not None:
                delta_ms = time.ticks_diff(now_ms, previous_time)
                if delta_ms > 0:
                    speed = (previous_distance - distance) / (delta_ms / 1000.0)
            track["previous_distance_m"] = distance
            track["previous_time_ms"] = now_ms
            track["distance_m"] = distance
            track["speed_mps"] = speed

            if class_id == PERSON_CLASS_ID:
                if distance <= PERSON_DANGER_DISTANCE_M:
                    risk = 2
                elif distance <= PERSON_SAFE_DISTANCE_M:
                    risk = 1
                else:
                    risk = 0
            elif distance <= DANGER_DISTANCE_M:
                risk = 2
            elif distance <= SAFE_DISTANCE_M and (
                previous_distance is None or speed >= ATTENTION_SPEED_MPS
            ):
                risk = 1
            else:
                risk = 0

            if risk == 0:
                track["candidate_risk"] = 0
                track["risk_frames"] = 0
                confirmed_risk = 0
            else:
                if risk == track.get("candidate_risk", 0):
                    track["risk_frames"] = track.get("risk_frames", 0) + 1
                else:
                    track["candidate_risk"] = risk
                    track["risk_frames"] = 1
                confirmed_risk = risk if track["risk_frames"] >= RISK_CONFIRM_FRAMES else 0

            track["risk"] = confirmed_risk
            if confirmed_risk > overall:
                overall = confirmed_risk
            results.append(track)
        return results, overall


class AlertController:
    def __init__(self):
        self.buzzer = None
        if (ENABLE_PERSON_BUZZER or ENABLE_VEHICLE_BUZZER) and YbBuzzer is not None:
            try:
                self.buzzer = YbBuzzer()
            except BaseException as error:
                print("buzzer init failed:", error)
        self.level = 0
        self.last_beep_ms = 0
        self.beep_until_ms = 0
        self.beep_active = False

    def update(self, level):
        if self.buzzer is None:
            return
        now_ms = time.ticks_ms()
        if level == 0:
            if self.beep_active or self.level != 0:
                self.buzzer.off()
            self.beep_active = False
            self.level = 0
            return

        frequency = 2700
        interval_ms = 700 if level == 1 else 220
        duration_ms = 180 if level == 1 else 240

        if self.level != level:
            if self.beep_active:
                self.buzzer.off()
                self.beep_active = False
            self.last_beep_ms = 0

        if self.beep_active and time.ticks_diff(now_ms, self.beep_until_ms) >= 0:
            self.buzzer.off()
            self.beep_active = False

        if not self.beep_active and (
            self.last_beep_ms == 0 or time.ticks_diff(now_ms, self.last_beep_ms) >= interval_ms
        ):
            self.buzzer.on(frequency, BUZZER_DUTY, 0)
            self.beep_active = True
            self.beep_until_ms = now_ms + duration_ms
            self.last_beep_ms = now_ms
        self.level = level

    def close(self):
        if self.buzzer is not None:
            try:
                self.buzzer.off()
            except BaseException:
                pass


def exitpoint():
    try:
        os.exitpoint()
    except AttributeError:
        pass


def main():
    if DISPLAY_MODE == "virt":
        pipeline = VirtualPipeLine(RGB888P_SIZE, DISPLAY_SIZE)
    else:
        pipeline = PipeLine(
            rgb888p_size=RGB888P_SIZE,
            display_size=DISPLAY_SIZE,
            display_mode=DISPLAY_MODE,
            debug_mode=0,
        )
    pipeline_ready = False
    vehicle_detector = None
    person_detector = None
    alert = None
    try:
        pipeline.create()
        pipeline_ready = True
        vehicle_detector = DetectionApp(
            KMODEL_PATH,
            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),
            rgb888p_size=RGB888P_SIZE,
            display_size=DISPLAY_SIZE,
            class_map=VEHICLE_CLASS_MAP,
            debug_mode=0,
        )
        vehicle_detector.config_preprocess()
        person_detector = DetectionApp(
            PERSON_KMODEL_PATH,
            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),
            rgb888p_size=RGB888P_SIZE,
            display_size=DISPLAY_SIZE,
            class_map=PERSON_CLASS_MAP,
            confidence_threshold=0.20,
            target_class_index=0,
            debug_mode=0,
        )
        person_detector.config_preprocess()
        print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "person_buzzer:", ENABLE_PERSON_BUZZER, "vehicle_buzzer:", ENABLE_VEHICLE_BUZZER, "display:", DISPLAY_MODE)
        tracker = SimpleTracker()
        risk_controller = RiskController(RGB888P_SIZE[0])
        alert = AlertController()
        startup_ms = time.ticks_ms()
        frame_count = 0
        fps_start_ms = startup_ms
        capture_ms = 0
        detect_ms = 0
        risk_ms = 0
        draw_ms = 0
        show_ms = 0

        while True:
            exitpoint()
            with ScopedTiming("total", 0):
                loop_start = time.ticks_ms()
                frame = pipeline.get_frame()
                capture_end = time.ticks_ms()
                vehicle_tensors = vehicle_detector.preprocess(frame)
                vehicle_results = vehicle_detector.inference(vehicle_tensors)
                vehicle_detections = vehicle_detector.postprocess(vehicle_results)
                person_tensors = person_detector.preprocess(frame)
                person_results = person_detector.inference(person_tensors)
                person_detections = person_detector.postprocess(person_results)
                detections = vehicle_detections + person_detections
                infer_end = time.ticks_ms()
                now_ms = infer_end
                tracks = tracker.update(detections, now_ms)
                current, overall_risk = risk_controller.evaluate(tracks, now_ms)
                person_alert = 0
                vehicle_alert = 0
                for track in current:
                    if track["risk"] <= 0:
                        continue
                    if track["class_id"] == PERSON_CLASS_ID:
                        if track["risk"] > person_alert:
                            person_alert = track["risk"]
                    else:
                        if track["risk"] > vehicle_alert:
                            vehicle_alert = track["risk"]

                alert_risk = 0
                if ENABLE_PERSON_BUZZER and person_alert > alert_risk:
                    alert_risk = person_alert
                if ENABLE_VEHICLE_BUZZER and vehicle_alert > alert_risk:
                    alert_risk = vehicle_alert

                if time.ticks_diff(now_ms, startup_ms) < STARTUP_GRACE_MS:
                    overall_risk = 0
                    alert_risk = 0
                track_end = time.ticks_ms()
                draw_detections = []
                for track in current:
                    draw_detections.append(
                        track["bbox"]
                        + [track["score"], track["class_id"], track["distance_m"], track["risk"]]
                    )
                vehicle_detector.draw_result(pipeline, draw_detections, overall_risk)
                draw_end = time.ticks_ms()
                pipeline.show_image()
                show_end = time.ticks_ms()
                alert.update(alert_risk)

                capture_ms += time.ticks_diff(capture_end, loop_start)
                detect_ms += time.ticks_diff(infer_end, capture_end)
                risk_ms += time.ticks_diff(track_end, infer_end)
                draw_ms += time.ticks_diff(draw_end, track_end)
                show_ms += time.ticks_diff(show_end, draw_end)

                frame_count += 1
                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:
                    detail_parts = []
                    for track in current:
                        detail_parts.append("{}:{:.2f}/{:.1f}m/W{}%/H{}%/R{}".format(
                            LABELS[track["class_id"]],
                            track["score"],
                            track["distance_m"],
                            int((track["bbox"][2] - track["bbox"][0]) * 100 / RGB888P_SIZE[0]),
                            int((track["bbox"][3] - track["bbox"][1]) * 100 / RGB888P_SIZE[1]),
                            track["risk"],
                        ))
                    detail_text = ";".join(detail_parts)
                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)
                    if elapsed_ms > 0:
                        print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} BUZZ={} DETAILS={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(
                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,
                            len(draw_detections),
                            len(vehicle_detections),
                            len(person_detections),
                            overall_risk,
                            alert_risk,
                            detail_text,
                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            detect_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            risk_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            draw_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            show_ms / float(DEBUG_LOG_EVERY_FRAMES),
                        ))
                    fps_start_ms = now_ms
                    capture_ms = 0
                    detect_ms = 0
                    risk_ms = 0
                    draw_ms = 0
                    show_ms = 0
                if frame_count % 10 == 0:
                    gc.collect()
    except KeyboardInterrupt:
        pass
    except BaseException as error:
        print("rear vehicle error:", error)
    finally:
        if alert is not None:
            alert.close()
        if person_detector is not None:
            person_detector.deinit()
        if vehicle_detector is not None:
            vehicle_detector.deinit()
        if pipeline_ready:
            pipeline.destroy()


if __name__ == "__main__":
    main()






