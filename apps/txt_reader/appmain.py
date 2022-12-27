from play32sys import path, battery, app
from play32hw import cpu
from micropython import const
from utime import sleep_ms
import gc
import hal_screen, hal_keypad, hal_battery, hal_sdcard
import book_reader, book_ui
from ui.select_file import select_file
from ui.dialog import dialog
from ui.select import select_menu
from ui.input_text import input_text

CPU_CONTEXT_FAST = cpu.cpu_speed_context(cpu.FAST)
CPU_CONTEXT_SLOW = cpu.cpu_speed_context(cpu.VERY_SLOW)

# const
SIZE_LOAD_PAGE = const(8)
SIZE_COMMIT_AFTER_FLIP = const(50)

# status
reader = None # type: book_reader.BookReader
data_path = "/data/txt_reader"

# operation
def main(app_name, *args, **kws):
    global reader, data_path
    hal_screen.init()
    hal_keypad.init()
    hal_battery.init()
    hal_sdcard.init()
    hal_sdcard.mount()
    reader = book_reader.BookReader(SIZE_COMMIT_AFTER_FLIP)
    data_path = path.get_data_path(app_name)
    # 进入主循环
    main_loop()

def open_book():
    # 加载文件
    data_dir =  "/sd" if path.exist("/sd") else data_path
    if not path.exist(data_dir):
        path.mkdirs(data_dir)
    txt_file_path = None
    pth = select_file(data_dir, "Text Reader", f_dir=False)
    if len(pth) < 1:
        dialog("Please select a text file.")
        return False
    if pth.endswith(".txt") or pth.endswith(".TXT"):
        txt_file_path = pth
    else:
        dialog("Please select a .txt file.")
        return False
    if txt_file_path == None:
        return False
    book_ui.render_message("正在加载书签")
    reader.load_book(txt_file_path)
    return True

def reader_loop():
    reader.render()
    with CPU_CONTEXT_SLOW:
        while True:
            for event in hal_keypad.get_key_event():
                event_type, key = hal_keypad.parse_key_event(event)
                if event_type != hal_keypad.EVENT_KEY_PRESS:
                    continue
                if key == hal_keypad.KEY_UP or key == hal_keypad.KEY_DOWN or key == hal_keypad.KEY_LEFT or key == hal_keypad.KEY_RIGHT:
                    with CPU_CONTEXT_FAST:
                        page_offset = 1 if key == hal_keypad.KEY_DOWN or key == hal_keypad.KEY_RIGHT else -1
                        reader.flip_page_by(page_offset)
                        reader.render()
                    reader.commit_bookmark_page()
                elif key == hal_keypad.KEY_A:
                    book_ui.render_status(battery.get_battery_level(), reader)
                    sleep_ms(1000)
                    reader.render()
                elif key == hal_keypad.KEY_B:
                    return
            if (reader != None) and (not reader.bookmark_loaded):
                with CPU_CONTEXT_FAST:
                    reader.load_bookmark(SIZE_LOAD_PAGE)
            battery.measure()

def get_status():
    if reader.book_loaded:
        bty = f"电量: {battery.get_battery_level()}%\n"
        if not reader.bookmark_loaded:
            return bty + \
                f"加载进度: {reader.bookmark_load_progress * 100:.3f}%"
        else:
            return bty + \
                f"第{reader.bookmark_current_page}页\n" + \
                f"共{reader.bookmark_total_page}页"
    else:
        return f"电量: {battery.get_battery_level()}%\n没有加载任何文本"

def main_loop():
    while True:
        gc.collect()
        sel = select_menu(get_status(), "Reader", ["打开书本", "跳转到", "退出阅读"], "确定", "继续阅读")
        if sel == 0:
            if open_book() and reader.book_loaded:
                reader_loop()
        elif sel == 1:
            if not reader.book_loaded:
                dialog("请先打开一本书")
                continue
            if not reader.bookmark_loaded:
                dialog("请等待书本加载完成")
                continue
            page = input_text(str(reader.bookmark_current_page), "Page")
            try:
                page_num = int(page)
                assert page_num >= 0
                assert page_num < reader.bookmark_total_page
            except:
                dialog("请输入合适的页码数字")
                continue
            reader.flip_page_by(page_num - reader.bookmark_current_page)
        elif sel == 2:
            if reader.book_loaded:
                reader.commit_bookmark_page()
            app.reset_and_run_app("")
        else:
            # 默认继续阅读
            if reader.book_loaded:
                reader_loop()
            else:
                dialog("请先打开一本书")
