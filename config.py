"""
Configuration management for Peloton Cadence Control
Loads settings from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for all settings"""

    # Cadence Settings
    CADENCE_THRESHOLD = int(os.getenv('CADENCE_THRESHOLD', '60'))
    GRACE_PERIOD_SECONDS = int(os.getenv('GRACE_PERIOD_SECONDS', '3'))
    ROLLING_AVERAGE_WINDOW = int(os.getenv('ROLLING_AVERAGE_WINDOW', '5'))

    # Bluetooth Settings
    CADENCE_SENSOR_MAC = os.getenv('CADENCE_SENSOR_MAC', '')
    CADENCE_SENSOR_NAME = os.getenv('CADENCE_SENSOR_NAME', 'Cadence')
    BLE_SCAN_TIMEOUT = int(os.getenv('BLE_SCAN_TIMEOUT', '10'))

    # UniFi Controller Settings
    UNIFI_HOST = os.getenv('UNIFI_HOST', '192.168.1.1')
    UNIFI_PORT = int(os.getenv('UNIFI_PORT', '8443'))
    UNIFI_USERNAME = os.getenv('UNIFI_USERNAME', '')
    UNIFI_PASSWORD = os.getenv('UNIFI_PASSWORD', '')
    UNIFI_SITE = os.getenv('UNIFI_SITE', 'default')
    UNIFI_VERIFY_SSL = os.getenv('UNIFI_VERIFY_SSL', 'false').lower() == 'true'

    # Peloton Settings
    PELOTON_IP = os.getenv('PELOTON_IP', '192.168.1.100')
    FIREWALL_RULE_ID = os.getenv('FIREWALL_RULE_ID', '')
    FIREWALL_RULE_NAME = os.getenv('FIREWALL_RULE_NAME', 'block_youtube_peloton')

    # Web Dashboard Settings
    WEB_DASHBOARD_ENABLED = os.getenv('WEB_DASHBOARD_ENABLED', 'true').lower() == 'true'
    WEB_DASHBOARD_PORT = int(os.getenv('WEB_DASHBOARD_PORT', '5000'))
    WEB_DASHBOARD_HOST = os.getenv('WEB_DASHBOARD_HOST', '0.0.0.0')

    # Logging Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'peloton_cadence.log')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.UNIFI_USERNAME:
            errors.append("UNIFI_USERNAME is required")
        if not cls.UNIFI_PASSWORD:
            errors.append("UNIFI_PASSWORD is required")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

    @classmethod
    def display(cls):
        """Display current configuration (hiding sensitive data)"""
        print("\n=== Peloton Cadence Control Configuration ===")
        print(f"Cadence Threshold: {cls.CADENCE_THRESHOLD} RPM")
        print(f"Grace Period: {cls.GRACE_PERIOD_SECONDS}s")
        print(f"Rolling Average Window: {cls.ROLLING_AVERAGE_WINDOW}s")
        print(f"\nUniFi Host: {cls.UNIFI_HOST}:{cls.UNIFI_PORT}")
        print(f"UniFi Site: {cls.UNIFI_SITE}")
        print(f"Peloton IP: {cls.PELOTON_IP}")
        print(f"\nWeb Dashboard: {'Enabled' if cls.WEB_DASHBOARD_ENABLED else 'Disabled'}")
        if cls.WEB_DASHBOARD_ENABLED:
            print(f"Dashboard Port: {cls.WEB_DASHBOARD_PORT}")
        print("=" * 45 + "\n")
