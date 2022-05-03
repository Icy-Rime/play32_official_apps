APP_NAME_ID = ""

# >>>> config memory <<<<
import gc
_threshold = (gc.mem_free() * 60) // 100 # 60% gc auto collect
gc.threshold(_threshold)
print("gc threshold has been set to", _threshold)
del _threshold

# >>>> main <<<<
try:
    from play32sys import app
    app._on_boot_(APP_NAME_ID)
    pass
except Exception as e:
    import usys, updater
    usys.print_exception(e)
    updater._on_enter_recovery_mode_()
print("==== End Main ====")
