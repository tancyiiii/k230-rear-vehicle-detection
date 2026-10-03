# -*- coding: utf-8 -*-
import os
import time
from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager

sensor = None
display_ready = False
media_ready = False
try:
    sensor = Sensor(id=2)
    sensor.reset()
    sensor.set_framesize(width=800, height=480)
    sensor.set_pixformat(Sensor.RGB565)
    Display.init(Display.ST7701, to_ide=True)
    display_ready = True
    MediaManager.init()
    media_ready = True
    sensor.run()
    print('LCD_ST7701_OK')
    while True:
        os.exitpoint()
        Display.show_image(sensor.snapshot())
        time.sleep_ms(5)
except KeyboardInterrupt:
    pass
except BaseException as e:
    print('LCD_ST7701_ERROR:', e)
finally:
    if sensor is not None:
        try: sensor.stop()
        except BaseException: pass
    if display_ready:
        try: Display.deinit()
        except BaseException: pass
    if media_ready:
        try: MediaManager.deinit()
        except BaseException: pass
