import os,time
from media.sensor import *
from media.media import MediaManager
s=Sensor(id=2); s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_2)
s.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR,chn=CAM_CHN_ID_2)
MediaManager.init(); s.run(); time.sleep(1)
img=s.snapshot(chn=CAM_CHN_ID_2)
print('SRC',img.format)
for name,obj in (('RGB565_DIRECT',img.to_rgb565()),('RGB888',img.to_rgb888()),('RGB888_TO_565',img.to_rgb888().to_rgb565())):
    try:
        print(name,obj.format,obj.get_statistics())
    except Exception as e:
        print(name,'ERR',e)
s.stop(); MediaManager.deinit()
