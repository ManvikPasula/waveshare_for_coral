import time
from periphery import GPIO, SPI, I2C

Device_SPI = 1
Device_I2C = 0

class CoralDevice:
    def __init__(self, spi_dev="/dev/spidev0.0", spi_mode=0, spi_max_speed=10000000,
                 rst_chip="/dev/gpiochip0", rst_line=27,
                 dc_chip="/dev/gpiochip0", dc_line=25,
                 bl_chip="/dev/gpiochip0", bl_line=18,
                 i2c_dev="/dev/i2c-1", i2c_address=0x3c):
        self.SPEED = spi_max_speed

        if Device_SPI == 1:
            self.Device = Device_SPI
            self.spi = SPI(spi_dev, spi_mode, spi_max_speed)
        else:
            self.Device = Device_I2C
            self.i2c = I2C(i2c_dev)
            self.address = i2c_address

        self.RST_PIN = GPIO(rst_chip, rst_line, "out")
        self.DC_PIN = GPIO(dc_chip, dc_line, "out")
        self.BL_PIN = GPIO(bl_chip, bl_line, "out")

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def digital_write(self, pin, value):
        pin.write(value)

    def digital_read(self, pin):
        return pin.read()

    def spi_writebyte(self, data):
        self.spi.transfer(data)

    def i2c_writebyte(self, reg, value):
        messages = [I2C.Message([reg, value])]
        self.i2c.transfer(self.address, messages)

    def module_init(self):
        self.digital_write(self.RST_PIN, False)
        if self.Device == Device_SPI:
            # SPI settings are configured during initialization
            pass
        self.digital_write(self.DC_PIN, False)
        return 0

    def module_exit(self):
        if self.Device == Device_SPI:
            self.spi.close()
        else:
            self.i2c.close()
        self.RST_PIN.close()
        self.DC_PIN.close()
        self.BL_PIN.close()

# Example Usage
if __name__ == "__main__":
    try:
        # Initialize the device
        device = CoralDevice()

        # Initialize the module
        device.module_init()

        # Perform some operations

        # Write a byte via SPI
        device.spi_writebyte([0xAA])

        # Write a byte via I2C
        device.i2c_writebyte(0x00, 0xFF)

    finally:
        # Clean up
        device.module_exit()
