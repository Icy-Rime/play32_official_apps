from graphic import framebuf_helper, ubmfont, bmfont
from buildin_resource import font
import hal_screen

WHITE = framebuf_helper.get_white_color(hal_screen.get_format())
SCR_W, SCR_H = hal_screen.get_size()
FNT: ubmfont.FontDrawUnicode = font.get_font_16px()
FNT_W, FNT_H = FNT.get_font_size()

def render_message(msg="加载中", process=0.0):
    frame = hal_screen.get_framebuffer()
    frame.fill(0)
    # prograss bar 7px
    frame.rect(0, 0, int((process * SCR_W) // 1), 7, WHITE, True)
    # text margin top 8px
    if len(bmfont.get_text_lines(msg, FNT, SCR_W, SCR_H)) == 1:
        t_width = bmfont.get_text_width(msg, FNT)
        t_offset = (SCR_W - t_width) // 2
    else:
        t_offset = 0
    FNT.draw_on_frame(msg, frame, t_offset, 8, WHITE, SCR_W, SCR_H-8)
    hal_screen.refresh()

def render_status(battery, reader):
    frame = hal_screen.get_framebuffer()
    frame.fill(0)
    FNT.draw_on_frame("电量:{}%".format(battery), frame, 0, 0, WHITE, SCR_W, FNT_H)
    if not reader.bookmark_loaded:
        FNT.draw_on_frame("加载进度:", frame, 0, FNT_H, WHITE, SCR_W, FNT_H)
        FNT.draw_on_frame("{:.3f}%".format(reader.bookmark_load_progress * 100), frame, 0, FNT_H * 2, WHITE, SCR_W, FNT_H)
    else:
        FNT.draw_on_frame("第{}页".format(reader.bookmark_current_page), frame, 0, FNT_H, WHITE, SCR_W, FNT_H)
        FNT.draw_on_frame("共{}页".format(reader.bookmark_total_page), frame, 0, FNT_H * 2, WHITE, SCR_W, FNT_H)
    hal_screen.refresh()
