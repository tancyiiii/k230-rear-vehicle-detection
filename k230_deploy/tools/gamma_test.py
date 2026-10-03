import os,time
from media.sensor import *
from media.media import MediaManager
s=Sensor(id=2); s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_0)
s.set_pixformat(PIXEL_FORMAT_RGB_565,chn=CAM_CHN_ID_0)
MediaManager.init(); s.run(); time.sleep(1)
img=s.snapshot(chn=CAM_CHN_ID_0)
st=img.get_statistics(); print('STAT_TYPE',type(st),'ATTRS',[x for x in dir(st) if not x.startswith('__')])
print('BEFORE',st.l_mean)
try:
    img.gamma(2.0)
    print('AFTER_GAMMA2',img.get_statistics().l_mean)
except Exception as e:
    print('GAMMA_ERR',e)
s.stop(); MediaManager.deinit()
