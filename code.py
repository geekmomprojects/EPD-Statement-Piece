# Write your code here :-)
import time
import board
import terminalio
import displayio
import random
from adafruit_display_text import label
from adafruit_display_shapes.circle import Circle

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

# Make sure your display driver is uncommented
import adafruit_il0373
#import adafruit_il91874
#import adafruit_ssd1608
#import adafruit_ssd1675
#import adafruit_il0398

# Set based on your display
FLEXIBLE = True
TRICOLOR = False
ROTATION = 90

# Used to ensure the display is free in CircuitPython
displayio.release_displays()

# Define the pins needed for display use
# This pinout is for a Feather M4 and may be different for other boards
# For the Metro/Shield, esc is board.D10 and dc is board.D9
spi = board.SPI()  # Uses SCK and MOSI
ecs = board.D12
dc = board.D11
rst = board.D9    # set to None for FeatherWing/Shield
busy = board.D7   # set to None for FeatherWing/Shield
srcs = board.D10
if TRICOLOR:
    highlight = 0xff0000 #third color is red (0xff0000)
else:
    highlight = 0x000000

# Create the displayio connection to the display pins
display_bus = displayio.FourWire(spi, command=dc, chip_select=ecs,
                                 reset=rst, baudrate=1000000)

time.sleep(1)  # Wait a bit

# Create the display object
#display = adafruit_ssd1608.SSD1608(display_bus, width=200, height=200,   # 1.54" HD Monochrome
#display = adafruit_ssd1675.SSD1675(display_bus, width=122, height=250,   # 2.13" HD Monochrome
#display = adafruit_il91874.IL91874(display_bus, width=264, height=176,   # 2.7" Tri-color
#display = adafruit_il0398.IL0398(display_bus, width=400, height=300,     # 4.2" Tri-color
#display = adafruit_il0373.IL0373(display_bus, width=152, height=152,     # 1.54" Tri-color
display = adafruit_il0373.IL0373(display_bus, width=296, height=128, swap_rams=FLEXIBLE, # 2.9" Tri-color OR Flexible Monochrome
#display = adafruit_il0373.IL0373(display_bus, width=212, height=104, swap_rams=FLEXIBLE, # 2.13" Tri-color OR Flexible Monochrome
                                 busy_pin=busy, rotation=ROTATION,
                                 highlight_color=highlight)

# Create a display group for our screen objects
g = displayio.Group(max_size=20)

BLACK = 0x000000
WHITE = 0xffffff
BLACK_INDEX = 0
WHITE_INDEX = 1

def fill_color(g,color=WHITE_INDEX):
    bitmap = displayio.Bitmap(display.width, display.height, 2)
    # Create a two color palette
    palette = displayio.Palette(2)
    palette[BLACK_INDEX] = BLACK
    palette[WHITE_INDEX] = WHITE
    bitmap.fill(color)
    # Create a TileGrid using the Bitmap and Palette
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    # Add the TileGrid to the Group
    g.append(tile_grid)

def random_circles(grp, ncircles, color=BLACK):
    ncircles = min(ncircles,20)
    for i in range(ncircles):
        fill=None
        #if random.random() > 0.7:
        #    fill = 0x000000
        grp.append(Circle(random.randint(10,display.width-10), random.randint(10,display.height-10),
                   random.randint(4,50),fill=fill,outline=color))

def corner_curliecues(grp):
    # Display a curly graphic from root directory of the CIRCUITPY drive
    f = open("image.bmp", "rb")
    pic = displayio.OnDiskBitmap(f)
    #Create a Tilegrid with the bitmap and put in the displayio group
    topleft = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter())
    botleft = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter(),
              x=0,y=(display.height-pic.height))
    botleft.flip_y = True
    topright = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter(),
              x=(display.width-pic.width),y=0)
    topright.flip_x = True
    botright = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter(),
              x=(display.width-pic.width),y=(display.height-pic.height))
    botright.flip_x = True
    botright.flip_y = True

    grp.append(topleft)
    grp.append(botleft)
    grp.append(topright)
    grp.append(botright)

def set_text(txt_area, text):
    txt_area.text = text
    box = txt_area.bounding_box
    txt_area.x = (display.width - txt_area.scale*box[2])//2
    txt_area.y = (display.height - box[3])//2
    #Gets bounding box tuple (x,y,w,h)
    #print(text_area.bounding_box)
    #print(text_area.anchor_point)
    #print(text_area.anchored_position)

def add_text_area(grp, maxchars=20,col=BLACK,bgcol=None):
    font = terminalio.FONT
    text_area = label.Label(font,text=" "*maxchars, color=col, background_color=bgcol, scale=3)

    #Gets bounding box tuple (x,y,w,h)
    #print(text_area.bounding_box)
    #print(text_area.anchor_point)
    #print(text_area.anchored_position)
    grp.append(text_area)
    return text_area

fill_color(g,WHITE_INDEX)
corner_curliecues(g)
message_area = add_text_area(g, 20)
set_text(message_area, "hi")
#random_circles(g,14)
display.show(g)
display.refresh()
last_display_time = time.monotonic()

while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass

    # Connected
    ble.stop_advertising()
    #print("CONNECTED")

    while ble.connected:
        # INCOMING (RX) check for incoming text
        if uart_server.in_waiting:
            raw_bytes = uart_server.read(uart_server.in_waiting)
            text = raw_bytes.decode().strip()
            #print("raw bytes =", raw_bytes)
            #print("RX:", text)
            if len(text) > 0:
                set_text(message_area, text)
                try:
                    if (time.monotonic() - last_display_time > 180):
                        print(" setting message ", text)
                        display.show(g)
                        display.refresh()
                        last_display_time = time.monotonic()
                    else:
                        print("too soon to display", text, "wait ", 180 - (time.monotonic() - last_display_time), " seconds")
                except RuntimeError as e:  # Refresh too soon
                    print(e)