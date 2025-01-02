import time
import board
import digitalio
import busio
from PIL import Image, ImageDraw, ImageFont
import logging

# OLED Dimensions
OLED_WIDTH = 128
OLED_HEIGHT = 64

class OLED_1in51:
    def __init__(self):
        # Initialize SPI
        self.spi = busio.SPI(board.SCLK, MOSI=board.MOSI)
        self.dc = digitalio.DigitalInOut(board.D25)
        self.dc.direction = digitalio.Direction.OUTPUT
        self.rst = digitalio.DigitalInOut(board.D27)
        self.rst.direction = digitalio.Direction.OUTPUT
        self.cs = digitalio.DigitalInOut(board.D8)
        self.cs.direction = digitalio.Direction.OUTPUT

        # Set OLED dimensions
        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT

    def command(self, cmd):
        self.dc.value = 0  # Command mode
        self.cs.value = 0
        self.spi.write(bytearray([cmd]))
        self.cs.value = 1

    def data(self, data):
        self.dc.value = 1  # Data mode
        self.cs.value = 0
        self.spi.write(bytearray(data))
        self.cs.value = 1

    def Init(self):
        logging.info("Initializing display...")
        self.reset()
        self.command(0xAE)  # Turn off OLED panel
        self.command(0x00)  # Set low column address
        self.command(0x10)  # Set high column address
        self.command(0xB0)  # Set page address
        self.command(0x81)  # Set contrast control
        self.command(0xCF)
        self.command(0xA1)  # Set segment remap
        self.command(0xC8)  # Set COM output scan direction
        self.command(0xA6)  # Set normal display
        self.command(0xA8)  # Set multiplex ratio
        self.command(0x3F)
        self.command(0xD3)  # Set display offset
        self.command(0x00)
        self.command(0xD5)  # Set display clock divide ratio
        self.command(0x80)
        self.command(0xD9)  # Set pre-charge period
        self.command(0xF1)
        self.command(0xDA)  # Set COM pins hardware configuration
        self.command(0x12)
        self.command(0xDB)  # Set VCOMH
        self.command(0x40)
        self.command(0xAF)  # Turn on OLED panel
        logging.info("Display initialized successfully.")

    def reset(self):
        self.rst.value = 1
        time.sleep(0.1)
        self.rst.value = 0
        time.sleep(0.1)
        self.rst.value = 1
        time.sleep(0.1)

    def getbuffer(self, image):
        buf = [0xFF] * ((self.width // 8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if imwidth == self.width and imheight == self.height:
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        buf[x + (y // 8) * self.width] &= ~(1 << (y % 8))
        return buf

    def ShowImage(self, pBuf):
        for page in range(0, 8):
            self.command(0xB0 + page)
            self.command(0x00)  # Set low column address
            self.command(0x10)  # Set high column address
            self.data(pBuf[self.width * page:self.width * (page + 1)])

    def clear(self):
        _buffer = [0xFF] * (self.width * self.height // 8)
        self.ShowImage(_buffer)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    disp = OLED_1in51()
    disp.Init()

    try:
        logging.info("Clearing display...")
        disp.clear()

        # Create an image with Pillow
        logging.info("Creating an image...")
        image = Image.new("1", (OLED_WIDTH, OLED_HEIGHT), "white")  # Create a blank white image
        draw = ImageDraw.Draw(image)

        # Draw a rectangle
        draw.rectangle((10, 10, 60, 30), outline="black", fill="black")

        # Draw a circle
        draw.ellipse((70, 10, 110, 50), outline="black", fill="white")

        # Draw text (optional)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)  # Use DejaVu font
        except IOError:
            logging.warning("Font not found. Using default font.")
            font = ImageFont.load_default()

        draw.text((10, 40), "Hello, OLED!", font=font, fill="black")

        # Convert the image to a buffer
        buffer = disp.getbuffer(image)

        # Display the image
        disp.ShowImage(buffer)
        logging.info("Image displayed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Exiting.")
