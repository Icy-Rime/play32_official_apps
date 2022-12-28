from graphic.pbm import read_image
from graphic.bmfont import FontDraw, arrange_text_gen
from framebuf import FrameBuffer, MONO_HLSB
from micropython import const

ASCII_0 = const(0x30)
ASCII_9 = const(0x39)
ASCII_T = const(9)
ASCII_N = const(10)
ASCII_R = const(13)

class NumberFont(FontDraw):
    def __init__(self, pbm_path):
        with open(pbm_path, "rb") as f:
            iw, ih, _, data, __ = read_image(f)
            img = FrameBuffer(data, iw, ih, MONO_HLSB)
        self._w = iw // 10
        self._h = ih
        self._img = img
    
    def get_char_width(self, unicode):
        return self._w

    def get_font_size(self):
        return (self._w, self._h)
    
    def draw_on_frame(self, text, frame, x, y, color=1, width_limit=-1, height_limit=-1) -> int:
        frame_pixel = frame.pixel
        img_pixel = self._img.pixel
        for count, unicode, cx, cy in arrange_text_gen(text, self, x, y, width_limit, height_limit):
            if unicode == ASCII_T or unicode == ASCII_N or unicode == ASCII_R:
                continue
            if unicode < ASCII_0 or unicode > ASCII_9:
                continue
            ascii_offset = unicode - ASCII_0
            fx = ascii_offset * self._w
            for iy in range(self._h):
                for ix in range(self._w):
                    if img_pixel(fx + ix, iy):
                        frame_pixel(cx + ix, cy + iy, color)
        return count
