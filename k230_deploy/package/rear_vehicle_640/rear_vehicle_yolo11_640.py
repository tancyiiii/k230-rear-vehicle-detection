# -*- coding: utf-8 -*-
"""K230 rear-vehicle recognition with YOLO11 and buzzer alerts.

Deploy layout on the K230 SD card:
    /sdcard/rear_vehicle/best_640.kmodel
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
KMODEL_PATH = "/sdcard/rear_vehicle/best_640.kmodel"
MODEL_INPUT_SIZE = 640
RGB888P_SIZE = [640, 640]
DISPLAY_SIZE = [800, 480]
DISPLAY_MODE = "virt"  # "virt" (CanMV IDE), "lcd" or "hdmi"

LABELS = ["bus", "car", "microbus", "motorbike", "pickup-van", "truck"]
VEHICLE_WIDTHS_M = [2.5, 1.8, 2.0, 0.8, 2.0, 2.5]

CONFIDENCE_THRESHOLD = 0.40
NMS_THRESHOLD = 0.40
MAX_BOXES = 50

HORIZONTAL_FOV_DEG = 120.0
SAFE_DISTANCE_M = 25.0
DANGER_DISTANCE_M = 10.0
ATTENTION_SPEED_MPS = 0.2

BUZZER_VOLUME = 100
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
    """Camera + IDE virtual display pipeline using the user's working media API."""

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
        self.sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)
        self.sensor.set_framesize(width=self.rgb888p_size[0], height=self.rgb888p_size[1], chn=CAM_CHN_ID_2)
        self.sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)
        Display.init(Display.VIRT, width=self.display_size[0], height=self.display_size[1], to_ide=True)
        MediaManager.init()
        self.sensor.run()
        self.ready = True

    def get_frame(self):
        self.osd_img = self.sensor.snapshot(chn=CAM_CHN_ID_0)
        ai_frame = self.sensor.snapshot(chn=CAM_CHN_ID_2)
        return ai_frame.to_numpy_ref()

    def show_image(self):
        Display.show_image(self.osd_img)

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
        self.x_factor = float(rgb888p_size[0]) / float(model_input_size[0])
        self.y_factor = float(rgb888p_size[1]) / float(model_input_size[1])
        self.colors = [
            (255, 220, 20, 60),
            (255, 119, 11, 32),
            (255, 0, 0, 142),
            (255, 0, 0, 230),
            (255, 106, 0, 228),
            (255, 0, 60, 100),
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
        if output.shape[0] <= 20:
            output = output.transpose()

        boxes_data = output[:, 0:4]
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
            left = int((cx - 0.5 * width) * self.x_factor)
            top = int((cy - 0.5 * height) * self.y_factor)
            right = int((cx + 0.5 * width) * self.x_factor)
            bottom = int((cy + 0.5 * height) * self.y_factor)

            left = _clamp(left, 0, self.rgb888p_size[0] - 1)
            top = _clamp(top, 0, self.rgb888p_size[1] - 1)
            right = _clamp(right, left + 1, self.rgb888p_size[0])
            bottom = _clamp(bottom, top + 1, self.rgb888p_size[1])
            if right - left < 4 or bottom - top < 4:
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
            x1, _, x2, _ = track["bbox"]
            width_px = max(1.0, float(x2 - x1))
            class_id = _clamp(int(track["class_id"]), 0, len(VEHICLE_WIDTHS_M) - 1)
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

            if distance <= DANGER_DISTANCE_M:
                risk = 2
            elif distance <= SAFE_DISTANCE_M and (
                previous_distance is None or speed >= ATTENTION_SPEED_MPS
            ):
                risk = 1
            else:
                risk = 0
            track["risk"] = risk
            if risk > overall:
                overall = risk
            results.append(track)
        return results, overall


class AlertController:
    def __init__(self):
        self.buzzer = None
        if YbBuzzer is not None:
            try:
                self.buzzer = YbBuzzer()
            except BaseException as error:
                print("buzzer init failed:", error)
        self.level = 0
        self.last_beep_ms = 0

    def update(self, level):
        if self.buzzer is None:
            return
        now_ms = time.ticks_ms()
        if level == 0:
            if self.level != 0:
                self.buzzer.off()
            self.level = 0
            return

        frequency = 1800 if level == 1 else 2600
        interval_ms = 1200 if level == 1 else 450
        duration_s = 0.08 if level == 1 else 0.12
        if self.level != level:
            self.last_beep_ms = 0
        if self.last_beep_ms == 0 or time.ticks_diff(now_ms, self.last_beep_ms) >= interval_ms:
            self.buzzer.on(frequency, BUZZER_VOLUME, duration_s)
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
    detector = None
    alert = None
    try:
        pipeline.create()
        pipeline_ready = True
        detector = DetectionApp(
            KMODEL_PATH,
            model_input_size=(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE),
            rgb888p_size=RGB888P_SIZE,
            display_size=DISPLAY_SIZE,
            debug_mode=0,
        )
        detector.config_preprocess()
        print("rear vehicle ready:", KMODEL_PATH, "display:", DISPLAY_MODE)
        tracker = SimpleTracker()
        risk_controller = RiskController(RGB888P_SIZE[0])
        alert = AlertController()
        frame_count = 0
        fps_start_ms = time.ticks_ms()
        capture_ms = 0
        pre_ms = 0
        kpu_ms = 0
        post_ms = 0
        risk_ms = 0
        draw_ms = 0
        show_ms = 0

        while True:
            exitpoint()
            with ScopedTiming("total", 0):
                loop_start = time.ticks_ms()
                frame = pipeline.get_frame()
                capture_end = time.ticks_ms()
                tensors = detector.preprocess(frame)
                pre_end = time.ticks_ms()
                results = detector.inference(tensors)
                kpu_end = time.ticks_ms()
                detections = detector.postprocess(results)
                infer_end = time.ticks_ms()
                now_ms = infer_end
                tracks = tracker.update(detections, now_ms)
                current, overall_risk = risk_controller.evaluate(tracks, now_ms)
                track_end = time.ticks_ms()
                draw_detections = []
                for track in current:
                    draw_detections.append(
                        track["bbox"]
                        + [track["score"], track["class_id"], track["distance_m"], track["risk"]]
                    )
                detector.draw_result(pipeline, draw_detections, overall_risk)
                draw_end = time.ticks_ms()
                pipeline.show_image()
                show_end = time.ticks_ms()
                alert.update(overall_risk)

                capture_ms += time.ticks_diff(capture_end, loop_start)
                pre_ms += time.ticks_diff(pre_end, capture_end)
                kpu_ms += time.ticks_diff(kpu_end, pre_end)
                post_ms += time.ticks_diff(infer_end, kpu_end)
                risk_ms += time.ticks_diff(track_end, infer_end)
                draw_ms += time.ticks_diff(draw_end, track_end)
                show_ms += time.ticks_diff(show_end, draw_end)

                frame_count += 1
                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:
                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)
                    if elapsed_ms > 0:
                        print("STATS FPS={:.2f} DET={} RISK={} ms(cap={:.1f},pre={:.1f},kpu={:.1f},post={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(
                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,
                            len(draw_detections),
                            overall_risk,
                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            pre_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            kpu_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            post_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            risk_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            draw_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            show_ms / float(DEBUG_LOG_EVERY_FRAMES),
                        ))
                    fps_start_ms = now_ms
                    capture_ms = 0
                    pre_ms = 0
                    kpu_ms = 0
                    post_ms = 0
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
        if detector is not None:
            detector.deinit()
        if pipeline_ready:
            pipeline.destroy()


if __name__ == "__main__":
    main()





