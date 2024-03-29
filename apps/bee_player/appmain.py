import hal_screen, hal_keypad, hal_buzz, uos
from play32sys import app, path
from graphic import framebuf_helper
from graphic.bmfont import get_text_width
from ui.utils import draw_buttons_at_last_line
from play32hw.buzz_note_sound import BuzzNoteSoundFile
from buildin_resource.font import get_font_8px, get_font_16px
FONT_8 = get_font_8px()
FONT_16 = get_font_16px()
COLOR_WHITE = framebuf_helper.get_white_color(hal_screen.get_format())

bee = None
buzz_sound_file = None
app_path = "/apps/bee_player"
sounds_path = "/apps/bee_player/sounds"
bns_list = []
current_playing = -1

def main(app_name, *args, **kws):
    global bee, app_path, sounds_path, current_playing
    hal_screen.init()
    hal_keypad.init()
    hal_buzz.init()
    app_path = path.get_app_path(app_name)
    if bee == None:
        sounds_path = path.join(app_path, "sounds")
        bns_list[:] = uos.listdir(sounds_path)
        bns_list.sort()
        if len(bns_list) > 0:
            current_playing = 0
        bee = hal_buzz.get_buzz_player()
        bee.init()
        render_status()
        main_loop()

def render_status():
    frame = hal_screen.get_framebuffer()
    frame.fill(0)
    scr_w, scr_h = hal_screen.get_size()
    fnt_w, fnt_h = FONT_8.get_font_size()
    # help text
    action_text = "Stop" if bee.is_playing else "Play"
    draw_buttons_at_last_line(frame, scr_w, scr_h, FONT_8, COLOR_WHITE, action_text, "Exit")
    # volume
    # FONT_8.draw_on_frame("↑/↓: Vol   {:1d}".format(bee.volume), frame, 0, scr_h - fnt_h*2, COLOR_WHITE)
    y_vol = scr_h - fnt_h*2
    w1 = get_text_width("↓", FONT_8)
    w2 = get_text_width("↑", FONT_8)
    FONT_8.draw_on_frame("↓", frame, 0, y_vol, COLOR_WHITE)
    FONT_8.draw_on_frame("↑", frame, scr_w - get_text_width("↑", FONT_8), y_vol, COLOR_WHITE)
    offset_volume = (scr_w - w1 - w2 - get_text_width("volume", FONT_8)) // 2 + w1
    FONT_8.draw_on_frame("volume", frame, offset_volume, y_vol, COLOR_WHITE)
    y_vol_bar = scr_h - fnt_h*3
    frame.vline(0, y_vol_bar, fnt_h, COLOR_WHITE)
    frame.vline(scr_w - 1, y_vol_bar, fnt_h, COLOR_WHITE)
    vol_bar_w = (scr_w - 4) * bee.volume // 9
    frame.rect(2, y_vol_bar + 1, vol_bar_w, fnt_h - 2, COLOR_WHITE, True)
    # playing status
    FONT_8.draw_on_frame("<", frame, 0, scr_h - fnt_h*4, COLOR_WHITE)
    FONT_8.draw_on_frame(">", frame, scr_w - FONT_8.get_char_width(b">"[0]), scr_h - fnt_h*4, COLOR_WHITE)
    status_text = "Playing" if bee.is_playing else "Stoped"
    status_text_width = get_text_width(status_text, FONT_8)
    status_text_offset_x = (scr_w - (fnt_w*2) - status_text_width) // 2 + fnt_w
    FONT_8.draw_on_frame(status_text, frame, status_text_offset_x, scr_h - fnt_h*4, COLOR_WHITE, scr_w - (fnt_w*2), fnt_h)
    # sounds name
    sound_name = bns_list[current_playing]
    FONT_16.draw_on_frame(sound_name, frame, 0, 0, COLOR_WHITE, scr_w, scr_h - fnt_h*4)
    hal_screen.refresh()

def keypad_event():
    global current_playing, buzz_sound_file
    for event in hal_keypad.get_key_event():
        event_type, key = hal_keypad.parse_key_event(event)
        if event_type == hal_keypad.EVENT_KEY_PRESS:
            if key == hal_keypad.KEY_B:
                bee.stop()
                bee.unload()
                bee.deinit()
                app.reset_and_run_app("") # press any key to reset
            elif key == hal_keypad.KEY_A:
                if bee.is_playing:
                    bee.stop()
                    bee.unload()
                else:
                    buzz_sound_file = BuzzNoteSoundFile(path.join(sounds_path, bns_list[current_playing]))
                    bee.load(buzz_sound_file)
                    bee.start(True)
            elif key in [hal_keypad.KEY_LEFT, hal_keypad.KEY_RIGHT]:
                if key == hal_keypad.KEY_LEFT:
                    current_playing -= 1
                    current_playing = len(bns_list) - 1 if current_playing < 0 else current_playing
                else:
                    current_playing += 1
                    current_playing = 0 if current_playing >= len(bns_list) else current_playing
                playing = bee.is_playing
                if playing:
                    bee.stop()
                bee.unload()
                if buzz_sound_file != None:
                    buzz_sound_file.file.close()
                buzz_sound_file = BuzzNoteSoundFile(path.join(sounds_path, bns_list[current_playing]))
                bee.load(buzz_sound_file)
                if playing:
                    bee.start(True)
            elif key in [hal_keypad.KEY_UP, hal_keypad.KEY_DOWN]:
                if key == hal_keypad.KEY_UP:
                    bee.set_volume(bee.volume + 1)
                else:
                    bee.set_volume(bee.volume - 1)
            render_status()

def main_loop():
    while True:
        keypad_event()
