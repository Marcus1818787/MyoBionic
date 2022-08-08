import imp
from gpiozero import Servo
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

from time import sleep
from Main import Hand

thumb = 21
index = 20
middle = 16
ring_little = 12
servo_delay = 0.7
threshold = 130

CLK = 4
MISO = 17
MOSI = 27
CS = 22
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
hand = Hand()
