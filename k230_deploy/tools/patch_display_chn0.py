from pathlib import Path
p=Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text=p.read_text(encoding="utf-8")
start=text.index("class VirtualPipeLine:")
end=text.index("class DetectionApp", start)
new='''class VirtualPipeLine:
    """Dual-channel camera pipeline for NPU inference and IDE display."""

    def __init__(self, rgb888p_size, display_size):
        self.rgb888p_size = [ALIGN_UP(rgb888p_size[0], 16), rgb888p_size[1]]
        self.display_size = [ALIGN_UP(display_size[0], 16), display_size[1]]
        self.sensor = None
        self.osd_img = None
        self.ready = False

    def create(self):
        self.sensor = Sensor(id=2)
        self.sensor.reset()
        self.sensor.set_framesize(width=self.display_size[0], height=self.display_size[1], chn=CAM_CHN_ID_0)
        self.sensor.set_pixformat(PIXEL_FORMAT_RGB_565, chn=CAM_CHN_ID_0)
        self.sensor.set_framesize(width=self.rgb888p_size[0], height=self.rgb888p_size[1], chn=CAM_CHN_ID_2)
        self.sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)
        Display.init(Display.VIRT, width=self.display_size[0], height=self.display_size[1], to_ide=True)
        MediaManager.init()
        self.sensor.run()
        self.ready = True

    def get_frame(self):
        self.osd_img = self.sensor.snapshot(chn=CAM_CHN_ID_0)
        try:
            self.osd_img.gamma(2.0)
        except BaseException:
            pass
        ai_frame = self.sensor.snapshot(chn=CAM_CHN_ID_2)
        return ai_frame.to_numpy_ref()

    def show_image(self):
        Display.show_image(self.osd_img)

    def destroy(self):
        if self.sensor is not None:
            try:
                self.sensor.stop()
            except BaseException:
                pass
        try:
            Display.deinit()
        except BaseException:
            pass
        try:
            MediaManager.deinit()
        except BaseException:
            pass


'''
text=text[:start]+new+text[end:]
p.write_text(text,encoding="utf-8")
print("patched",p)
