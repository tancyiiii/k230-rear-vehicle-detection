import os, time
from media.sensor import *
from media.media import MediaManager
s=Sensor(id=2)
s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_2)
s.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR,chn=CAM_CHN_ID_2)
MediaManager.init(); s.run(); time.sleep(1)
img=s.snapshot(chn=CAM_CHN_ID_2)
print('RAW_FMT',img.format)
print('RAW_STATS',img.get_statistics())
rgb=img.to_rgb565()
print('RGB_FMT',rgb.format)
print('RGB_STATS',rgb.get_statistics())
print('SENSOR_METHODS',[x for x in dir(s) if 'exposure' in x.lower() or 'gain' in x.lower()])
s.stop(); MediaManager.deinit()
