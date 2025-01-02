from periphery import GPIO, SPI, I2C
import time
from PIL import Image, ImageDraw, ImageFont
import logging

# Constants for SPI and I2C
Device_SPI = 1
Device_I2C = 0

# OLED Dimensions
OLED_WIDTH = 128
OLED_HEIGHT = 64

class CoralDevice:
    def __init__(self, spi_device="/dev/spidev0.0", spi_freq=10000000, rst_pin=27, dc_pin=25, bl_pin=18, i2c_device=None):
        self.Device = Device_SPI if spi_device else Device_I2C
        self.SPEED = spi_freq
        self.RST_PIN = GPIO("/dev/gpiochip0", rst_pin, "out")
        self.DC_PIN = GPIO("/dev/gpiochip0", dc_pin, "out")
        self.spi = SPI(spi_device, 0, self.SPEED) if self.Device == Device_SPI else None
        self.i2c = I2C(i2c_device) if self.Device == Device_I2C else None

    def digital_write(self, pin, value):
        pin.write(bool(value))

    def spi_writebyte(self, data):
        if self.Device == Device_SPI:
            self.spi.transfer(bytearray(data))

    def i2c_writebyte(self, reg, value):
        if self.Device == Device_I2C:
            self.i2c.transfer(0x3C, [reg, value])

    def module_exit(self):
        self.RST_PIN.write(False)
        self.DC_PIN.write(False)
        if self.Device == Device_SPI:
            self.spi.close()
        if self.Device == Device_I2C:
            self.i2c.close()
        self.RST_PIN.close()
        self.DC_PIN.close()

class OLED_1in51(CoralDevice):
    def command(self, cmd):
        self.digital_write(self.DC_PIN, 0)
        if self.Device == Device_SPI:
            self.spi_writebyte([cmd])
        else:
            self.i2c_writebyte(0x00, cmd)

    def Init(self):
        if self.Device == Device_SPI and not self.spi:
            logging.error("SPI device not initialized.")
            return -1

        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT

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
        self.digital_write(self.RST_PIN, True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN, False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN, True)
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
            if self.Device == Device_SPI:
                self.digital_write(self.DC_PIN, True)
                self.spi_writebyte(pBuf[self.width * page:self.width * (page + 1)])

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
        time.sleep(3)
        logging.info("Image displayed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        disp.module_exit()
