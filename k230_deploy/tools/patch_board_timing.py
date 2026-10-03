from pathlib import Path

base = Path(r"C:\k230_deploy\board")
old = '''        frame_count = 0
        fps_start_ms = time.ticks_ms()

        while True:
            exitpoint()
            with ScopedTiming("total", 0):
                frame = pipeline.get_frame()
                detections = detector.run(frame)
                now_ms = time.ticks_ms()
                tracks = tracker.update(detections, now_ms)
                current, overall_risk = risk_controller.evaluate(tracks, now_ms)
                draw_detections = []
                for track in current:
                    draw_detections.append(
                        track["bbox"]
                        + [track["score"], track["class_id"], track["distance_m"], track["risk"]]
                    )
                detector.draw_result(pipeline, draw_detections, overall_risk)
                pipeline.show_image()
                alert.update(overall_risk)
                frame_count += 1
                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:
                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)
                    if elapsed_ms > 0:
                        print("STATS FPS={:.2f} DET={} RISK={}".format(
                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,
                            len(draw_detections),
                            overall_risk,
                        ))
                    fps_start_ms = now_ms
                if frame_count % 10 == 0:
                    gc.collect()
'''
new = '''        frame_count = 0
        fps_start_ms = time.ticks_ms()
        capture_ms = 0
        infer_ms = 0
        other_ms = 0
        draw_ms = 0
        show_ms = 0

        while True:
            exitpoint()
            with ScopedTiming("total", 0):
                loop_start = time.ticks_ms()
                frame = pipeline.get_frame()
                capture_end = time.ticks_ms()
                detections = detector.run(frame)
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
                infer_ms += time.ticks_diff(infer_end, capture_end)
                other_ms += time.ticks_diff(track_end, infer_end)
                draw_ms += time.ticks_diff(draw_end, track_end)
                show_ms += time.ticks_diff(show_end, draw_end)

                frame_count += 1
                if DEBUG_LOG_EVERY_FRAMES > 0 and frame_count % DEBUG_LOG_EVERY_FRAMES == 0:
                    elapsed_ms = time.ticks_diff(now_ms, fps_start_ms)
                    if elapsed_ms > 0:
                        print("STATS FPS={:.2f} DET={} RISK={} ms(cap={:.1f},inf={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(
                            DEBUG_LOG_EVERY_FRAMES * 1000.0 / elapsed_ms,
                            len(draw_detections),
                            overall_risk,
                            capture_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            infer_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            other_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            draw_ms / float(DEBUG_LOG_EVERY_FRAMES),
                            show_ms / float(DEBUG_LOG_EVERY_FRAMES),
                        ))
                    fps_start_ms = now_ms
                    capture_ms = 0
                    infer_ms = 0
                    other_ms = 0
                    draw_ms = 0
                    show_ms = 0
                if frame_count % 10 == 0:
                    gc.collect()
'''
for name in ("rear_vehicle_yolo11.py", "rear_vehicle_yolo11_640.py"):
    path = base / name
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"block not found: {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("patched", path)
