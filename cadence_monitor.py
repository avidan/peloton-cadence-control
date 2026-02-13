#!/usr/bin/env python3
"""
Peloton Cadence Monitor - Main Control Loop
Monitors cadence from BLE sensor and controls YouTube access via UniFi firewall
"""
import asyncio
import time
from collections import deque
from logger import setup_logger
from config import Config
from ble_reader import CadenceSensor
from unifi_controller import UniFiController

logger = setup_logger('cadence_monitor')


class CadenceMonitor:
    """
    Main controller that monitors cadence and controls YouTube blocking
    """

    def __init__(self):
        self.sensor = CadenceSensor()
        self.controller = UniFiController()
        self.cadence_history = deque(maxlen=Config.ROLLING_AVERAGE_WINDOW)
        self.current_cadence = 0
        self.youtube_blocked = None  # None = unknown, True = blocked, False = unblocked
        self.last_state_change = 0
        self.running = False

    async def initialize(self):
        """Initialize connections to sensor and UniFi controller"""
        logger.info("Initializing Peloton Cadence Monitor...")
        Config.display()

        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return False

        # Verify UniFi OS API access
        logger.info("Connecting to UniFi OS...")
        if not self.controller.verify_access():
            logger.error("Failed to connect to UniFi OS")
            logger.error("Please check your UNIFI_API_KEY in .env file")
            return False

        # Initialize rule ID if not set
        if not Config.FIREWALL_RULE_ID:
            logger.info("Firewall rule ID not configured, searching by name...")
            rule_id = self.controller.initialize_rule_id()
            if not rule_id:
                logger.error(f"Could not find firewall rule '{Config.FIREWALL_RULE_NAME}'")
                logger.error("Please create the firewall rule in UniFi Controller first")
                return False
            self.controller.firewall_rule_id = rule_id

        # Get initial rule status
        self.youtube_blocked = self.controller.get_rule_status()
        if self.youtube_blocked is None:
            logger.error("Could not get firewall rule status")
            return False

        logger.info(f"Current YouTube block status: {'BLOCKED' if self.youtube_blocked else 'ALLOWED'}")

        # Connect to BLE cadence sensor
        logger.info("Scanning for cadence sensor...")
        if not await self.sensor.connect():
            logger.error("Failed to connect to cadence sensor")
            logger.error("Please check that:")
            logger.error("  1. The sensor is powered on")
            logger.error("  2. The sensor is not connected to another device")
            logger.error("  3. Bluetooth is enabled on this device")
            return False

        # Start cadence notifications
        logger.info("Starting cadence monitoring...")
        if not await self.sensor.start_notifications(callback=self._cadence_update):
            logger.error("Failed to start cadence notifications")
            return False

        logger.info("✓ Initialization complete!")
        logger.info(f"Monitoring cadence... Threshold: {Config.CADENCE_THRESHOLD} RPM")
        return True

    def _cadence_update(self, cadence):
        """
        Callback for cadence updates from BLE sensor

        Args:
            cadence: Current cadence in RPM
        """
        self.current_cadence = cadence
        self.cadence_history.append(cadence)

    def get_average_cadence(self):
        """
        Calculate rolling average cadence

        Returns:
            Average cadence over the rolling window
        """
        if not self.cadence_history:
            return 0
        return sum(self.cadence_history) / len(self.cadence_history)

    def should_block_youtube(self):
        """
        Determine if YouTube should be blocked based on current cadence

        Returns:
            True if YouTube should be blocked, False otherwise
        """
        avg_cadence = self.get_average_cadence()

        # Not enough data yet - default to BLOCKED for safety
        if len(self.cadence_history) < Config.ROLLING_AVERAGE_WINDOW:
            logger.debug(f"Waiting for more data ({len(self.cadence_history)}/{Config.ROLLING_AVERAGE_WINDOW})")
            return True

        # Check against threshold
        should_block = avg_cadence < Config.CADENCE_THRESHOLD

        logger.debug(f"Cadence: {self.current_cadence} RPM | Avg: {avg_cadence:.1f} RPM | "
                    f"Threshold: {Config.CADENCE_THRESHOLD} RPM | Should block: {should_block}")

        return should_block

    def can_change_state(self):
        """
        Check if enough time has passed since last state change (grace period)

        Returns:
            True if state can be changed
        """
        time_since_change = time.time() - self.last_state_change
        return time_since_change >= Config.GRACE_PERIOD_SECONDS

    async def update_youtube_block(self):
        """
        Update YouTube block status based on current cadence
        """
        should_block = self.should_block_youtube()

        # Check if state needs to change
        if should_block == self.youtube_blocked:
            # No change needed
            return

        # Check grace period
        if not self.can_change_state():
            time_remaining = Config.GRACE_PERIOD_SECONDS - (time.time() - self.last_state_change)
            logger.debug(f"Grace period active, waiting {time_remaining:.1f}s before state change")
            return

        # Change state
        avg_cadence = self.get_average_cadence()

        if should_block:
            logger.warning(f"⚠ Cadence too low ({avg_cadence:.1f} RPM < {Config.CADENCE_THRESHOLD} RPM) - BLOCKING YouTube")
            success = self.controller.enable_rule()
        else:
            logger.info(f"✓ Cadence sufficient ({avg_cadence:.1f} RPM >= {Config.CADENCE_THRESHOLD} RPM) - ALLOWING YouTube")
            success = self.controller.disable_rule()

        if success:
            self.youtube_blocked = should_block
            self.last_state_change = time.time()
        else:
            logger.error("Failed to update firewall rule")

    async def monitor_loop(self):
        """
        Main monitoring loop
        """
        self.running = True
        logger.info("Starting monitor loop...")

        try:
            while self.running:
                # Check if still connected
                if not self.sensor.is_connected():
                    logger.warning("Lost connection to cadence sensor - BLOCKING YouTube for safety")

                    # Block YouTube immediately when sensor disconnects
                    if not self.youtube_blocked:
                        if self.controller.enable_rule():
                            self.youtube_blocked = True
                            self.last_state_change = time.time()
                            logger.warning("⚠ YouTube BLOCKED due to sensor disconnect")

                    # Clear cadence history since we have no data
                    self.cadence_history.clear()
                    self.current_cadence = 0

                    # Attempt reconnect
                    logger.info("Attempting to reconnect to sensor...")
                    if not await self.sensor.connect():
                        logger.error("Reconnection failed, waiting 10s before retry...")
                        await asyncio.sleep(10)
                        continue
                    else:
                        logger.info("✓ Reconnected to sensor successfully")
                        # Restart notifications
                        await self.sensor.start_notifications(callback=self._cadence_update)

                # Update YouTube block status
                await self.update_youtube_block()

                # Status update every 10 iterations
                if int(time.time()) % 10 == 0:
                    avg_cadence = self.get_average_cadence()
                    status = "BLOCKED" if self.youtube_blocked else "ALLOWED"
                    logger.info(f"Status: Cadence={self.current_cadence} RPM | "
                               f"Avg={avg_cadence:.1f} RPM | YouTube={status}")

                # Wait before next check
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up connections"""
        logger.info("Shutting down...")
        self.running = False

        # Disconnect from sensor
        if self.sensor.is_connected():
            await self.sensor.disconnect()

        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    monitor = CadenceMonitor()

    # Initialize
    if not await monitor.initialize():
        logger.error("Initialization failed")
        return 1

    # Run monitor loop
    await monitor.monitor_loop()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)
