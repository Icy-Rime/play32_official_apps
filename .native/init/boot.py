import usys, esp, machine, micropython
usys.path[:] = ['lib', '', '/lib', '/', '.frozen']
esp.osdebug(None)
machine.freq(240000000)
micropython.alloc_emergency_exception_buf(100)
