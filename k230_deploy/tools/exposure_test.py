import os, time
from media.sensor import *
from media.media import MediaManager
s=Sensor(id=2); s.reset()
s.set_framesize(width=320,height=320,chn=CAM_CHN_ID_2)
s.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR,chn=CAM_CHN_ID_2)
MediaManager.init(); s.run(); time.sleep(1)
for fn_name in ('set_auto_exposure','set_auto_gain'):
    try:
        getattr(s,fn_name)(True)
        print(fn_name,'OK')
    except Exception as e:
        print(fn_name,'ERR',e)
time.sleep(1)
for b in (0,25,50,75,100,-4,0,4):
    try:
        s.set_brightness(b)
        time.sleep(0.6)
        img=s.snapshot(chn=CAM_CHN_ID_2)
        rgb=img.to_rgb565()
        st=rgb.get_statistics()
        print('BRIGHT',b,'LMEAN',st.get('l_mean'),'LMAX',st.get('l_max'),'LSTD',st.get('l_stdev'))
    except Exception as e:
        print('BRIGHT',b,'ERR',e)
s.stop(); MediaManager.deinit()
