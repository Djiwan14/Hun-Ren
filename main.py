from logic import *
from guis import *

logic = Logic(serial_port='COM5', baud_rate=9600)

gui = Guis(logic)

gui.start_gui()
