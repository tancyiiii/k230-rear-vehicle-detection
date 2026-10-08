# -*- coding: utf-8 -*-
"""K230 power-on autostart entry for rear-vehicle recognition."""

import gc
import os
import sys
import time


APP_DIR = "/sdcard/rear_vehicle"
APP_MODULE = "rear_vehicle_yolo11"
BOOT_ERROR_PATHS = (
    "/sdcard/boot_error.txt",
    APP_DIR + "/boot_error.txt",
)


def _write_boot_error(error):
    message = "{}: {}\n".format(type(error).__name__, error)
    for path in BOOT_ERROR_PATHS:
        try:
            with open(path, "w") as fp:
                fp.write(message)
            return
        except BaseException:
            pass


def _exists(path):
    try:
        os.stat(path)
        return True
    except BaseException:
        return False


# Allow the SD card, camera and audio codec to finish initializing after power-on.
try:
    time.sleep_ms(1200)
except AttributeError:
    time.sleep(1.2)

sys.path.insert(0, APP_DIR)

try:
    print("AUTOSTART: rear vehicle recognition")
    if not _exists(APP_DIR):
        raise OSError("missing application directory: " + APP_DIR)
    if not _exists(APP_DIR + "/" + APP_MODULE + ".py"):
        raise OSError("missing application: " + APP_DIR + "/" + APP_MODULE + ".py")
    gc.collect()
    app = __import__(APP_MODULE)
    app.main()
except KeyboardInterrupt:
    pass
except BaseException as error:
    print("AUTOSTART ERROR:", error)
    _write_boot_error(error)

