"""
Bluetooth Low Energy reader for cadence sensors
Supports standard Cycling Speed and Cadence (CSC) Service
"""
import asyncio
from bleak import BleakClient, BleakScanner
from logger import setup_logger
from config import Config

logger = setup_logger('ble_reader')

# Standard Bluetooth SIG UUIDs
CSC_SERVICE_UUID = "00001816-0000-1000-8000-00805f9b34fb"  # Cycling Speed and Cadence
CSC_MEASUREMENT_UUID = "00002a5b-0000-1000-8000-00805f9b34fb"  # CSC Measurement

class CadenceSensor:
    """
    Bluetooth LE Cadence Sensor Reader
    """

    def __init__(self):
        self.client = None
        self.device = None
        self.cadence = 0
        self.last_crank_revolutions = None
        self.last_crank_event_time = None
        self.connected = False
        self.cadence_callback = None

    async def scan_for_sensor(self, timeout=10):
        """
        Scan for BLE cadence sensors

        Args:
            timeout: Scan timeout in seconds

        Returns:
            List of discovered devices
        """
        logger.info(f"Scanning for BLE devices (timeout: {timeout}s)...")

        devices = await BleakScanner.discover(timeout=timeout)

        cadence_devices = []
        for device in devices:
            logger.debug(f"Found device: {device.name} ({device.address})")

            # Check if device matches configured MAC or name
            if Config.CADENCE_SENSOR_MAC and device.address.lower() == Config.CADENCE_SENSOR_MAC.lower():
                logger.info(f"Found configured sensor: {device.name} ({device.address})")
                cadence_devices.append(device)
            elif Config.CADENCE_SENSOR_NAME and Config.CADENCE_SENSOR_NAME.lower() in (device.name or '').lower():
                logger.info(f"Found sensor by name: {device.name} ({device.address})")
                cadence_devices.append(device)
            elif device.name and any(keyword in device.name.lower() for keyword in ['cadence', 'speed', 'wahoo', 'garmin', 'polar']):
                logger.info(f"Found potential cadence sensor: {device.name} ({device.address})")
                cadence_devices.append(device)

        if not cadence_devices:
            logger.warning("No cadence sensors found")
            logger.info("Please check that:")
            logger.info("  1. The sensor is powered on")
            logger.info("  2. The sensor is not connected to another device")
            logger.info("  3. You're within Bluetooth range")

        return cadence_devices

    async def connect(self, device=None):
        """
        Connect to cadence sensor

        Args:
            device: BleakDevice to connect to (optional, will scan if not provided)

        Returns:
            True if connected successfully
        """
        if not device:
            # Scan for device
            devices = await self.scan_for_sensor(timeout=Config.BLE_SCAN_TIMEOUT)
            if not devices:
                logger.error("No cadence sensors found during scan")
                return False
            device = devices[0]  # Use first found device

        self.device = device
        logger.info(f"Connecting to {device.name} ({device.address})...")

        try:
            self.client = BleakClient(device.address)
            await self.client.connect()
            self.connected = True
            logger.info(f"Successfully connected to {device.name}")

            # List all services and characteristics for debugging
            services = self.client.services
            logger.debug("Available services:")
            for service in services:
                logger.debug(f"  Service: {service.uuid}")
                for char in service.characteristics:
                    logger.debug(f"    Characteristic: {char.uuid} (Properties: {char.properties})")

            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False

    async def start_notifications(self, callback=None):
        """
        Start receiving cadence notifications

        Args:
            callback: Optional callback function to call with cadence updates
        """
        if not self.connected or not self.client:
            logger.error("Not connected to sensor")
            return False

        self.cadence_callback = callback

        try:
            # Start notifications on CSC Measurement characteristic
            await self.client.start_notify(CSC_MEASUREMENT_UUID, self._notification_handler)
            logger.info("Started cadence notifications")
            return True

        except Exception as e:
            logger.error(f"Failed to start notifications: {e}")
            logger.info("Attempting to find CSC characteristic manually...")

            # Try to find CSC service manually
            for service in self.client.services:
                if CSC_SERVICE_UUID.lower() in service.uuid.lower():
                    logger.info(f"Found CSC service: {service.uuid}")
                    for char in service.characteristics:
                        if "notify" in [p.lower() for p in char.properties]:
                            logger.info(f"Trying characteristic: {char.uuid}")
                            try:
                                await self.client.start_notify(char.uuid, self._notification_handler)
                                logger.info(f"Successfully started notifications on {char.uuid}")
                                return True
                            except Exception as e2:
                                logger.debug(f"Failed on {char.uuid}: {e2}")

            logger.error("Could not start notifications on any characteristic")
            return False

    def _notification_handler(self, sender, data):
        """
        Handle CSC Measurement notifications

        CSC Measurement format (from Bluetooth SIG spec):
        - Byte 0: Flags
          - Bit 0: Wheel Revolution Data Present
          - Bit 1: Crank Revolution Data Present
        - If Crank Revolution Data Present:
          - Bytes 1-2: Cumulative Crank Revolutions (uint16)
          - Bytes 3-4: Last Crank Event Time (uint16, 1/1024s resolution)
        """
        try:
            if len(data) < 1:
                return

            flags = data[0]
            crank_data_present = (flags & 0x02) != 0

            if not crank_data_present:
                logger.debug("No crank data in this packet")
                return

            if len(data) < 5:
                logger.warning(f"Insufficient data for crank measurement: {len(data)} bytes")
                return

            # Parse crank revolutions (uint16, little-endian)
            crank_revolutions = int.from_bytes(data[1:3], byteorder='little', signed=False)

            # Parse last crank event time (uint16, little-endian, 1/1024 second resolution)
            crank_event_time = int.from_bytes(data[3:5], byteorder='little', signed=False)

            # Calculate cadence if we have previous data
            if self.last_crank_revolutions is not None and self.last_crank_event_time is not None:
                # Handle rollover (uint16 wraps at 65536)
                rev_diff = crank_revolutions - self.last_crank_revolutions
                if rev_diff < 0:
                    rev_diff += 65536

                time_diff = crank_event_time - self.last_crank_event_time
                if time_diff < 0:
                    time_diff += 65536

                if time_diff > 0:
                    # Calculate RPM
                    # time_diff is in 1/1024 seconds
                    # Convert to minutes: (time_diff / 1024) / 60
                    # RPM = revolutions / minutes
                    time_minutes = (time_diff / 1024.0) / 60.0
                    if time_minutes > 0:
                        self.cadence = int(rev_diff / time_minutes)
                        logger.debug(f"Cadence: {self.cadence} RPM (revs: {rev_diff}, time: {time_diff}/1024s)")

                        # Call callback if provided
                        if self.cadence_callback:
                            self.cadence_callback(self.cadence)

            # Update last values
            self.last_crank_revolutions = crank_revolutions
            self.last_crank_event_time = crank_event_time

        except Exception as e:
            logger.error(f"Error parsing cadence data: {e}")

    async def disconnect(self):
        """Disconnect from sensor"""
        if self.client and self.connected:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from sensor")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.connected = False

    def get_cadence(self):
        """Get current cadence reading"""
        return self.cadence

    def is_connected(self):
        """Check if connected to sensor"""
        return self.connected


async def test_sensor():
    """Test function to scan and connect to cadence sensor"""
    sensor = CadenceSensor()

    # Scan for devices
    devices = await sensor.scan_for_sensor(timeout=10)

    if not devices:
        print("No cadence sensors found")
        return

    print(f"\nFound {len(devices)} device(s):")
    for i, device in enumerate(devices):
        print(f"  {i+1}. {device.name} ({device.address})")

    # Connect to first device
    if await sensor.connect(devices[0]):
        print(f"\nConnected! Starting cadence monitoring...")

        def cadence_update(rpm):
            print(f"Cadence: {rpm} RPM")

        await sensor.start_notifications(callback=cadence_update)

        # Monitor for 60 seconds
        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping...")

        await sensor.disconnect()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_sensor())
