import subprocess
from PyQt5.QtCore import QRect

XDOTOOL = "xdotool"

def xdotool(*args):
	return subprocess.check_output([XDOTOOL] + list(map(str, args))).decode().strip()

def get_window_name(window_id):
	return xdotool("getwindowname", window_id)

def get_active_window():
	return int(xdotool("getactivewindow"))

def window_move(window_id, x, y):
	xdotool("windowmove", window_id, x, y)

def window_resize(window_id, w, h):
	xdotool("windowsize", window_id, w, h)

def window_move_resize(window_id, rect):
	window_move(window_id, rect.left(), rect.top())
	window_resize(window_id, rect.width(), rect.height())

def window_raise(window_id):
	xdotool("windowraise", window_id)

def get_display_rectangle():
	size = xdotool("getdisplaygeometry")
	(w, h) = map(int, size.split())
	return QRect(0, 0, w, h)
