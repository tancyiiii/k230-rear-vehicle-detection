from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
t=p.read_text(encoding="utf-8")
t=t.replace("ENABLE_BUZZER = False\nBUZZER_DUTY = 50\n", "ENABLE_PERSON_BUZZER = True\nENABLE_VEHICLE_BUZZER = False\nBUZZER_DUTY = 50\n", 1)
t=t.replace(
    "        if ENABLE_BUZZER and YbBuzzer is not None:\n",
    "        if (ENABLE_PERSON_BUZZER or ENABLE_VEHICLE_BUZZER) and YbBuzzer is not None:\n",
    1,
)
t=t.replace(
    'print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "buzzer:", ENABLE_BUZZER, "display:", DISPLAY_MODE)',
    'print("rear vehicle ready:", KMODEL_PATH, "person:", PERSON_KMODEL_PATH, "person_buzzer:", ENABLE_PERSON_BUZZER, "vehicle_buzzer:", ENABLE_VEHICLE_BUZZER, "display:", DISPLAY_MODE)',
    1,
)
old='''                current, overall_risk = risk_controller.evaluate(tracks, now_ms)
                if time.ticks_diff(now_ms, startup_ms) < STARTUP_GRACE_MS:
                    overall_risk = 0
                track_end = time.ticks_ms()
'''
new='''                current, overall_risk = risk_controller.evaluate(tracks, now_ms)
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
'''
if old not in t:
    raise SystemExit("risk/main alert block not found")
t=t.replace(old,new,1)
t=t.replace("                alert.update(overall_risk)\n", "                alert.update(alert_risk)\n", 1)
t=t.replace(
    'print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} DETAILS={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n',
    'print("STATS FPS={:.2f} DET={} VEH={} PERSON={} RISK={} BUZZ={} DETAILS={} ms(cap={:.1f},detect={:.1f},risk={:.1f},draw={:.1f},show={:.1f})".format(\n',
    1,
)
t=t.replace(
    '                            overall_risk,\n                            detail_text,\n',
    '                            overall_risk,\n                            alert_risk,\n                            detail_text,\n',
    1,
)
p.write_text(t,encoding="utf-8")
print("patched",p)
