# -*- coding: utf-8 -*-
"""K230 power-on autostart entry for rear-vehicle recognition."""

import gc
import sys

sys.path.insert(0, "/sdcard/rear_vehicle")

try:
    print("AUTOSTART: rear vehicle recognition")
    gc.collect()
    import rear_vehicle_yolo11 as app
    app.main()
except KeyboardInterrupt:
    pass
except BaseException as error:
    print("AUTOSTART ERROR:", error)
    try:
        with open("/sdcard/rear_vehicle/boot_error.txt", "w") as fp:
            fp.write(str(error))
    except BaseException:
        pass

