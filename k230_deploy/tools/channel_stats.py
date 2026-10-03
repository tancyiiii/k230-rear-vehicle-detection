import os, time
from media.sensor import *
from media.media import MediaManager
s=Sensor(id=2); s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_0)
s.set_pixformat(PIXEL_FORMAT_RGB_565,chn=CAM_CHN_ID_0)
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_2)
s.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR,chn=CAM_CHN_ID_2)
MediaManager.init(); s.run(); time.sleep(1)
for chn,name in ((CAM_CHN_ID_0,'CH0_RGB565'),(CAM_CHN_ID_2,'CH2_RGBP888')):
    try:
        img=s.snapshot(chn=chn)
        print(name,'STATS',img.get_statistics())
    except Exception as e:
        print(name,'ERR',e)
s.stop(); MediaManager.deinit()
