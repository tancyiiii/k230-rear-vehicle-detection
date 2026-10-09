# -*- coding: utf-8 -*-
"""K230 rear-vehicle recognition with YOLO11 and speaker alerts.

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
    import _thread
except BaseException:
    _thread = None

from array import array

try:
    from ybUtils.YbSpeaker import YbSpeaker
except BaseException:
    YbSpeaker = None

try:
    from ybUtils.YbBuzzer import YbBuzzer
except BaseException:
    YbBuzzer = None

try:
    import media.pyaudio as pyaudio
except BaseException:
    try:
        import pyaudio
    except BaseException:
        pyaudio = None

try:
    from serial_control import SerialControl
except BaseException:
    SerialControl = None


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

ENABLE_PERSON_SPEAKER = True
ENABLE_VEHICLE_SPEAKER = True
SPEAKER_SAMPLE_RATE = 44100
SPEAKER_FRAME_SAMPLES = 1024
# PCM prompts have a low speech average level; apply a strong boost for audibility.
# _boost_pcm() hard-limits samples to avoid 16-bit overflow.
SPEAKER_AMPLITUDE = 1.0
# Raise the speech average level while keeping hard limiting for 16-bit output.
SPEECH_GAIN = 12.0
SPEECH_PERSON_PCM_PATH = "/sdcard/rear_vehicle/attention_person.pcm"
SPEECH_VEHICLE_PCM_PATH = "/sdcard/rear_vehicle/attention_vehicle.pcm"
USE_SPEECH_PROMPT = True
ALERT_REPEAT_COOLDOWN_MS = 5000
SPEECH_REPEAT_ATTENTION_MS = ALERT_REPEAT_COOLDOWN_MS
SPEECH_REPEAT_DANGER_MS = ALERT_REPEAT_COOLDOWN_MS
# Keep the hardware buzzer on the tested 2700 Hz tone.
BUZZER_TONE = "classic"
BUZZER_TONE_PRESETS = {
    "piercing": {
        "frequencies": (4000, 5200),
        "duration_s": 0.055,
        "gap_ms": 25,
        "beeps": 2,
        "waveform": "square",
    },
    "classic": {
        "frequencies": (2800,),
        "duration_s": 0.08,
        "gap_ms": 70,
        "beeps": 2,
        "waveform": "sine",
    },
    "alarm": {
        "frequencies": (3200, 4800),
        "duration_s": 0.07,
        "gap_ms": 30,
        "beeps": 6,
        "waveform": "square",
    },
    "soft": {
        "frequencies": (2200,),
        "duration_s": 0.12,
        "gap_ms": 100,
        "beeps": 2,
        "waveform": "sine",
    },
}
BUZZER_PRESET = BUZZER_TONE_PRESETS.get(
    BUZZER_TONE, BUZZER_TONE_PRESETS["piercing"]
)
# Match ``voice -1.py``: a warm 2700 Hz two-beep alert at full volume.
BUZZER_FREQUENCY = 2700
BUZZER_VOLUME = 100
BUZZER_DURATION_S = 0.08
BUZZER_GAP_MS = 70
BUZZER_BEEPS = 2

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


def _make_tone_bytes(
    frequency,
    duration_ms,
    amplitude=SPEAKER_AMPLITUDE,
    waveform="square",
):
    """Generate a selectable sine, square, or sawtooth buzzer tone."""
    sample_count = int(SPEAKER_SAMPLE_RATE * duration_ms / 1000)
    amplitude_value = int(32767 * amplitude)
    samples = array("h")
    for index in range(sample_count):
        phase = (frequency * index / SPEAKER_SAMPLE_RATE) % 1.0
        if waveform == "sine":
            value = int(amplitude_value * math.sin(2.0 * math.pi * phase))
        elif waveform == "saw":
            value = int(amplitude_value * (2.0 * phase - 1.0))
        else:
            fundamental = 1.0 if phase < 0.5 else -1.0
            third = 1.0 if (phase * 3.0) % 1.0 < 0.5 else -1.0
            fifth = 1.0 if (phase * 5.0) % 1.0 < 0.5 else -1.0
            value = int(
                amplitude_value
                * (0.55 * fundamental + 0.30 * third + 0.15 * fifth)
            )
        samples.append(value)
        samples.append(value)
    return bytes(samples)


def _boost_pcm(data, gain):
    """Increase 16-bit little-endian stereo PCM level with hard limiting."""
    if gain <= 1.0:
        return data
    samples = array("h")
    for offset in range(0, len(data) - 1, 2):
        sample = data[offset] | (data[offset + 1] << 8)
        if sample >= 32768:
            sample -= 65536
        sample = int(sample * gain)
        if sample > 32767:
            sample = 32767
        elif sample < -32768:
            sample = -32768
        samples.append(sample)
    return bytes(samples)


class AlertController:
    """Non-blocking K230 speaker alert using the onboard codec and YbSpeaker."""

    def __init__(self):
        self.level = 0
        self._closed = False
        self._stream = None
        self._audio = None
        self._speaker = None
        self._thread = None
        self._thread_done = False
        self._fallback_last_ms = 0
        self._frame_bytes = SPEAKER_FRAME_SAMPLES * 4
        self._silence = bytes(self._frame_bytes)
        self._speech_person = None
        self._speech_vehicle = None
        self._prompt_kind = 0
        self._fallback_tone = None
        self._buzzer = None
        self._buzzer_active = False
        self._buzzer_kind = 0
        self._last_buzzer_ms = 0
        self._last_buzzer_kind = 0
        self._last_prompt_ms = 0
        self._last_prompt_key = 0

        # Keep the hardware chirp independent from the PCM speaker path.
        if YbBuzzer is not None:
            try:
                self._buzzer = YbBuzzer()
            except BaseException as error:
                print("buzzer init failed:", error)

        if not (ENABLE_PERSON_SPEAKER or ENABLE_VEHICLE_SPEAKER):
            return
        if pyaudio is None or YbSpeaker is None:
            print("speaker unavailable: pyaudio=", pyaudio, "YbSpeaker=", YbSpeaker)
            return

        try:
            self._speaker = YbSpeaker()
            self._speaker.enable()
            self._audio = pyaudio.PyAudio()
            # The official K230 example configures audio VB buffers before
            # MediaManager.init(), then opens the output stream after it.
            self._audio.initialize(SPEAKER_FRAME_SAMPLES)
            self._fallback_tone = _make_tone_bytes(
                BUZZER_FREQUENCY,
                int(BUZZER_DURATION_S * 1000),
                waveform=BUZZER_PRESET["waveform"],
            )
            if USE_SPEECH_PROMPT:
                for path, attribute in (
                    (SPEECH_PERSON_PCM_PATH, "_speech_person"),
                    (SPEECH_VEHICLE_PCM_PATH, "_speech_vehicle"),
                ):
                    try:
                        with open(path, "rb") as speech_file:
                            speech = speech_file.read()
                        if not speech or len(speech) % 4 != 0:
                            raise ValueError("invalid stereo PCM data")
                        setattr(self, attribute, _boost_pcm(speech, SPEECH_GAIN))
                        print("speech prompt loaded:", path, len(speech))
                    except BaseException as error:
                        setattr(self, attribute, None)
                        print("speech prompt load failed:", path, error)
        except BaseException as error:
            print("speaker prepare failed:", error)
            self._safe_close(close_buzzer=False)

    def start(self):
        if self._audio is None or self._stream is not None:
            return
        try:
            self._stream = self._audio.open(
                format=self._audio.get_format_from_width(2),
                channels=2,
                rate=44100,
                input=0,
                output=1,
                frames_per_buffer=SPEAKER_FRAME_SAMPLES,
            )
            if _thread is not None:
                self._thread = _thread.start_new_thread(self._run, ())
            print("speaker ready: rate=44100")
        except BaseException as error:
            print("speaker start failed:", error)
            self._safe_close(close_buzzer=False)

    def _start_buzzer_alert(self, kind):
        if self._buzzer is None or _thread is None:
            return False
        self._buzzer_kind = int(kind)
        if self._buzzer_active:
            return False
        now_ms = time.ticks_ms()
        buzzer_key = self.level * 10 + self._buzzer_kind
        if (
            self._last_buzzer_kind == buzzer_key
            and self._last_buzzer_ms != 0
            and time.ticks_diff(now_ms, self._last_buzzer_ms) < ALERT_REPEAT_COOLDOWN_MS
        ):
            return False
        self._buzzer_active = True
        try:
            _thread.start_new_thread(self._buzzer_alert_worker, ())
            self._last_buzzer_kind = buzzer_key
            self._last_buzzer_ms = now_ms
            return True
        except BaseException as error:
            self._buzzer_active = False
            print("buzzer thread start failed:", error)
            return False

    def _buzzer_alert_worker(self):
        try:
            active_kind = self._buzzer_kind
            for beep_index in range(BUZZER_BEEPS):
                if (
                    self._closed
                    or self.level <= 0
                    or self._buzzer_kind != active_kind
                ):
                    return
                self._buzzer.on(BUZZER_FREQUENCY, BUZZER_VOLUME, BUZZER_DURATION_S)
                time.sleep_ms(int(BUZZER_DURATION_S * 1000))
                if beep_index + 1 < BUZZER_BEEPS:
                    time.sleep_ms(BUZZER_GAP_MS)
        except BaseException as error:
            print("buzzer alert failed:", error)
        finally:
            try:
                self._buzzer.off()
            except BaseException:
                pass
            self._buzzer_active = False

    def update(self, level, person_present=False, prompt_kind=0):
        level = int(level)
        prompt_kind = int(prompt_kind)
        self.level = level
        self._buzzer_kind = prompt_kind if level > 0 else 0
        if level > 0 and prompt_kind > 0:
            self._start_buzzer_alert(prompt_kind)
        elif self._buzzer is not None:
            try:
                self._buzzer.off()
            except BaseException:
                pass
        if self._stream is None:
            return
        self._prompt_kind = prompt_kind
        if self._thread is not None:
            return

        now_ms = time.ticks_ms()
        if level <= 0:
            self._fallback_last_ms = 0
            return
        interval_ms = 700 if level == 1 else 280
        if self._fallback_last_ms == 0 or time.ticks_diff(now_ms, self._fallback_last_ms) >= interval_ms:
            self._write_buffer(self._fallback_tone, level)
            self._fallback_last_ms = now_ms

    def _write_buffer(self, data, level, prompt_kind=0):
        if self._stream is None or not data:
            return
        position = 0
        while position < len(data):
            if self._closed or self.level != level or self._prompt_kind != prompt_kind:
                return
            chunk = data[position:position + self._frame_bytes]
            if len(chunk) < self._frame_bytes:
                chunk = chunk + self._silence[len(chunk):]
            try:
                self._stream.write(chunk)
            except BaseException as error:
                print("speaker write failed:", error)
                self._safe_close(close_buzzer=False)
                return
            position += self._frame_bytes

    def _wait_for_level(self, level, duration_ms, prompt_kind=None):
        end_ms = time.ticks_ms() + duration_ms
        while (
            not self._closed
            and self.level == level
            and (prompt_kind is None or self._prompt_kind == prompt_kind)
        ):
            if time.ticks_diff(end_ms, time.ticks_ms()) <= 0:
                break
            time.sleep_ms(10)
        return self.level == level and (
            prompt_kind is None or self._prompt_kind == prompt_kind
        )

    def _run(self):
        try:
            while not self._closed:
                level = self.level
                if level <= 0:
                    time.sleep_ms(10)
                    continue
                prompt_kind = self._prompt_kind
                speech = (
                    self._speech_person
                    if prompt_kind == 1
                    else self._speech_vehicle
                    if prompt_kind == 2
                    else None
                )
                repeat_ms = (
                    SPEECH_REPEAT_ATTENTION_MS
                    if level == 1
                    else SPEECH_REPEAT_DANGER_MS
                )
                prompt_key = level * 10 + prompt_kind
                now_ms = time.ticks_ms()
                can_play = (
                    self._last_prompt_key != prompt_key
                    or self._last_prompt_ms == 0
                    or time.ticks_diff(now_ms, self._last_prompt_ms) >= repeat_ms
                )
                if speech is not None:
                    if can_play:
                        self._write_buffer(speech, level, prompt_kind)
                        self._last_prompt_key = prompt_key
                        self._last_prompt_ms = now_ms
                    self._wait_for_level(level, repeat_ms, prompt_kind)
                else:
                    if can_play:
                        self._write_buffer(self._fallback_tone, level, prompt_kind)
                        self._last_prompt_key = prompt_key
                        self._last_prompt_ms = now_ms
                    self._wait_for_level(level, repeat_ms, prompt_kind)
        except BaseException as error:
            print("speaker thread stopped:", error)
        finally:
            self._thread_done = True

    def _safe_close(self, close_buzzer=True):
        if self._stream is not None:
            try:
                self._stream.stop_stream()
            except BaseException:
                pass
            try:
                self._stream.close()
            except BaseException:
                pass
            self._stream = None
        if self._audio is not None:
            try:
                self._audio.terminate()
            except BaseException:
                pass
            self._audio = None
        if self._speaker is not None:
            try:
                self._speaker.disable()
            except BaseException:
                pass
            self._speaker = None
        if close_buzzer and self._buzzer is not None:
            try:
                self._buzzer.off()
            except BaseException:
                pass
            self._buzzer = None

    def close(self):
        self._closed = True
        if self._thread is not None:
            for _ in range(20):
                if self._thread_done:
                    break
                time.sleep_ms(50)
            self._thread = None
        self._safe_close()


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
    alert = AlertController()
    control = SerialControl() if SerialControl is not None else None
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
        print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "person_speaker:", ENABLE_PERSON_SPEAKER, "vehicle_speaker:", ENABLE_VEHICLE_SPEAKER, "display:", DISPLAY_MODE)
        tracker = SimpleTracker()
        risk_controller = RiskController(RGB888P_SIZE[0])
        alert.start()
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
            if control is not None and not control.poll():
                alert.update(0, False, 0)
                time.sleep_ms(20)
                continue
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
                if ENABLE_PERSON_SPEAKER and person_alert > alert_risk:
                    alert_risk = person_alert
                if ENABLE_VEHICLE_SPEAKER and vehicle_alert > alert_risk:
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
                prompt_kind = 0
                if person_alert > 0 and alert_risk > 0:
                    prompt_kind = 1
                elif vehicle_alert > 0 and alert_risk > 0:
                    prompt_kind = 2
                alert.update(alert_risk, person_alert > 0 and alert_risk > 0, prompt_kind)

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
                        print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} SPK={} DETAILS={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(
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
        if control is not None:
            control.close()
        if person_detector is not None:
            person_detector.deinit()
        if vehicle_detector is not None:
            vehicle_detector.deinit()
        if pipeline_ready:
            pipeline.destroy()


if __name__ == "__main__":
    main()






