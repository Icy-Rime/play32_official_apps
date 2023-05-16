import hal_screen, hal_keypad, hal_battery, hal_network
from buildin_resource.font import get_font_8px
from graphic import framebuf_helper
from graphic.bmfont import get_text_width
from play32sys import app, path, battery
from play32hw import cpu, hw_config
from utime import sleep_ms, ticks_ms, ticks_diff, ticks_add, time as local_time, gmtime, mktime
from number import NumberFont
from ui.progress import progress_gen
from ui.dialog import dialog
from ui.select import select_list
from ui.input import input_slide
from micropython import const
from net.ntptime import time as net_time

WHITE = framebuf_helper.get_white_color(hal_screen.get_format())
SCRW, SCRH = hal_screen.get_size()
BIG_NUM = None # type: NumberFont
F8 = get_font_8px()
CONNECT_TIMEOUT = const(10_000) # ms

time_offset = 0
utc_offset = 8
use_cpu_sleep = False

def main(app_name, *args, **kws):
    global BIG_NUM
    hal_screen.init()
    hal_keypad.init()
    hal_battery.init()
    battery.init_battery_value_cache(8)
    app_root = path.get_app_path(app_name)
    BIG_NUM = NumberFont(path.join(app_root, "images", "terminus24x48.pbm"))
    main_loop()

def render_time():
    time_now = gmtime(time_offset + local_time() + (utc_offset * 3600))
    frame = hal_screen.get_framebuffer()
    frame.fill(0)
    date_str = f"{time_now[0]}年{time_now[1]}月{time_now[2]}日"
    # render date
    text_width = get_text_width(date_str, F8)
    F8.draw_on_frame(date_str, frame, (SCRW - text_width) // 2, 0, WHITE)
    # render time
    HSCRW = SCRW // 2
    FW, FH = BIG_NUM.get_font_size()
    hr_str = str(time_now[3])
    if len(hr_str) < 2:
        hr_str = "0" + hr_str
    minu_str = str(time_now[4])
    if len(minu_str) < 2:
        minu_str = "0" + minu_str
    text_width = get_text_width(hr_str, BIG_NUM)
    BIG_NUM.draw_on_frame(hr_str, frame, HSCRW - 1 - text_width, SCRH - FH, WHITE)
    text_width = get_text_width(minu_str, BIG_NUM)
    BIG_NUM.draw_on_frame(minu_str, frame, HSCRW + 1 + (FW//8), SCRH - FH, WHITE)
    FH8D1 = FH // 8
    frame.rect(HSCRW - 1, SCRH - FH + FH8D1, 2, FH - FH8D1*2, WHITE, 1)
    frame.rect(HSCRW - 1, SCRH - FH + FH8D1*3, 2, FH - FH8D1*6, 0, 1)
    # render battery
    bat_value = battery.get_battery_level()
    bat_width = int(SCRW * bat_value / 100)
    frame. hline((SCRW - bat_width) // 2, SCRH - 1, bat_width, WHITE)
    hal_screen.refresh()

def sync_network_time():
    global time_offset
    wlan = hal_network.connect()
    try:
        p = progress_gen("", "Syncing Time")
        start_at = ticks_ms()
        next(p)
        while not wlan.isconnected():
            next(p)
            if ticks_diff(ticks_ms(), start_at) > CONNECT_TIMEOUT:
                raise Exception("Connect Timeout")
        time_offset = net_time() - local_time()
    finally:
        hal_network.deactive_all()

def get_next_minute_ms():
    current_seconds = gmtime(time_offset + local_time())[5]
    next_minus_ms = ticks_ms()
    next_minus_ms = (next_minus_ms // 1000) * 1000
    next_minus_ms = ticks_add(next_minus_ms, (60 - current_seconds) * 1000)
    return next_minus_ms + 10

def show_time_loop():
    next_min_at = get_next_minute_ms()
    render_time()
    while True:
        battery.measure()
        for event in hal_keypad.get_key_event():
            event_type, key = hal_keypad.parse_key_event(event)
            if event_type == hal_keypad.EVENT_KEY_PRESS:
                if key == hal_keypad.KEY_B:
                    return # return to main menu
        if ticks_diff(next_min_at, ticks_ms()) <= 0:
            render_time()
            next_min_at = ticks_add(next_min_at, 60000)
        next_ms = 1000 - (ticks_ms() % 1000)
        if use_cpu_sleep:
            cpu.sleep(next_ms)
        else:
            sleep_ms(next_ms)

def main_loop():
    global time_offset, utc_offset, use_cpu_sleep
    if hw_config.get_model() in [ hw_config.MODEL_INITIAL ]:
        use_cpu_sleep = True
    while True:
        sel = select_list("Menu", ["Show Time", "Set Time Zone", "Sync Network Time", "Adjust Time", "Quit"], "Confirm", "Show Time")
        if sel <= 0:
            show_time_loop()
        elif sel == 1:
            sel = select_list("UTC Offset", [ str(i) if i <= 0 else "+" + str(i) for i in range(-12, 15) ], "Confirm", "Back")
            if sel < 0:
                continue
            num = sel - 12
            utc_offset = num
        elif sel == 2:
            try:
                sync_network_time()
            except:
                dialog("Failed to sync time, please config WIFI first.", "Error")
        elif sel == 3:
            d_items = list(gmtime(time_offset + local_time() + (utc_offset * 3600)))
            d_names = ["Year", "Month", "Day", "Hour", "Minute", "Second"]
            d_starts = [2000, 1, 1, 0, 0, 0]
            d_size = [3000, 12, 31, 23, 59, 59]
            step = 0
            while step >= 0 and step < 6:
                num = input_slide(d_names[step], "Next", "Back", d_starts[step], d_size[step], d_items[step])
                if num < d_starts[step]:
                    step -= 1
                else:
                    d_items[step] = num
                    step += 1
            if step < 0:
                continue
            set_time = mktime(tuple(d_items))
            time_offset = set_time - local_time() - (utc_offset * 3600)
        elif sel == 4:
            app.reset_and_run_app("")