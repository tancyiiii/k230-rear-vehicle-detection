import os, time
from media.sensor import *
from media.media import MediaManager

s=Sensor(id=2)
s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_2)
s.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR,chn=CAM_CHN_ID_2)
MediaManager.init()
s.run()
time.sleep(1)
img=s.snapshot(chn=CAM_CHN_ID_2)
print('TYPE',type(img))
print('ATTRS',[x for x in dir(img) if not x.startswith('__')])
try:
    print('NUMPY', img.to_numpy_ref().shape)
except Exception as e:
    print('NUMPY_ERR',e)
try:
    out=img.copy(x_scale=2.0,y_scale=2.0)
    print('COPY_OK',out)
    print('OUT_ATTRS',[x for x in dir(out) if not x.startswith('__')])
except Exception as e:
    print('COPY_ERR',e)
s.stop(); MediaManager.deinit()
