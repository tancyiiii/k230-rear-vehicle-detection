from pathlib import Path

path = Path(r"C:\k230_deploy\board\rear_vehicle_yolo11.py")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "from libs.PipeLine import PipeLine, ScopedTiming",
    "from libs.PipeLine import PipeLine, ScopedTiming\nfrom media.display import *\nfrom media.media import *\nfrom media.sensor import *",
)
text = text.replace(
    'DISPLAY_MODE = "lcd"  # "lcd" or "hdmi"',
    'DISPLAY_MODE = "virt"  # "virt" (CanMV IDE), "lcd" or "hdmi"',
)

virtual_class = '''class VirtualPipeLine:
    """Camera + IDE virtual display pipeline using the user's working media API."""

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

anchor = "class DetectionApp(AIBase):"
if "class VirtualPipeLine" not in text:
    text = text.replace(anchor, virtual_class + anchor, 1)

old_pipeline = '''    pipeline = PipeLine(
        rgb888p_size=RGB888P_SIZE,
        display_size=DISPLAY_SIZE,
        display_mode=DISPLAY_MODE,
        debug_mode=0,
    )'''
new_pipeline = '''    if DISPLAY_MODE == "virt":
        pipeline = VirtualPipeLine(RGB888P_SIZE, DISPLAY_SIZE)
    else:
        pipeline = PipeLine(
            rgb888p_size=RGB888P_SIZE,
            display_size=DISPLAY_SIZE,
            display_mode=DISPLAY_MODE,
            debug_mode=0,
        )'''
if old_pipeline not in text:
    raise SystemExit("pipeline init block not found")
text = text.replace(old_pipeline, new_pipeline, 1)

path.write_text(text, encoding="utf-8")
print("patched", path)
