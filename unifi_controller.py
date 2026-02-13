"""
UniFi OS API client for managing traffic rules via API key
"""
import requests
import urllib3
from logger import setup_logger
from config import Config

# Disable SSL warnings if verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger('unifi_controller')


class UniFiController:
    """
    UniFi OS API Client
    Manages traffic rules via API key authentication (v2 API)
    """

    def __init__(self):
        self.base_url = f"https://{Config.UNIFI_HOST}:{Config.UNIFI_PORT}"
        self.api_path = f"/proxy/network/v2/api/site/{Config.UNIFI_SITE}/trafficrules"
        self.session = requests.Session()
        self.session.verify = Config.UNIFI_VERIFY_SSL
        self.session.headers.update({
            'X-API-Key': Config.UNIFI_API_KEY,
        })
        self.firewall_rule_id = Config.FIREWALL_RULE_ID

    def verify_access(self):
        """
        Verify API key works by fetching traffic rules

        Returns:
            True if API key is valid and controller is reachable
        """
        try:
            logger.debug(f"Verifying API access to UniFi OS at {self.base_url}")
            rules = self.get_traffic_rules()
            if rules is not None:
                logger.info("Successfully connected to UniFi OS")
                return True
            else:
                logger.error("API key authentication failed")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def get_traffic_rules(self):
        """
        Get all traffic rules

        Returns:
            List of traffic rules or None if failed
        """
        try:
            url = f"{self.base_url}{self.api_path}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                rules = response.json()
                logger.debug(f"Retrieved {len(rules)} traffic rules")
                return rules
            else:
                logger.error(f"Failed to get traffic rules: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting traffic rules: {e}")
            return None

    def find_rule_by_name(self, rule_name):
        """
        Find traffic rule by description

        Args:
            rule_name: Description of the rule to find

        Returns:
            Rule dict or None if not found
        """
        rules = self.get_traffic_rules()
        if not rules:
            return None

        for rule in rules:
            if rule.get('description', '').lower() == rule_name.lower():
                logger.info(f"Found rule '{rule_name}': {rule.get('_id')}")
                return rule

        logger.warning(f"Rule '{rule_name}' not found")
        return None

    def enable_rule(self, rule_id=None):
        """
        Enable (activate) a traffic rule

        Args:
            rule_id: Rule ID to enable (uses configured rule_id if not provided)

        Returns:
            True if successful
        """
        if not rule_id:
            rule_id = self.firewall_rule_id

        if not rule_id:
            logger.error("No rule ID provided or configured")
            return False

        return self._update_rule(rule_id, enabled=True)

    def disable_rule(self, rule_id=None):
        """
        Disable (deactivate) a traffic rule

        Args:
            rule_id: Rule ID to disable (uses configured rule_id if not provided)

        Returns:
            True if successful
        """
        if not rule_id:
            rule_id = self.firewall_rule_id

        if not rule_id:
            logger.error("No rule ID provided or configured")
            return False

        return self._update_rule(rule_id, enabled=False)

    def _update_rule(self, rule_id, enabled):
        """
        Internal method to update rule enabled state

        Args:
            rule_id: Rule ID to update
            enabled: True to enable, False to disable

        Returns:
            True if successful
        """
        try:
            # First, get the current rule to preserve other settings
            rules = self.get_traffic_rules()
            if not rules:
                logger.error("Could not retrieve traffic rules")
                return False

            rule = None
            for r in rules:
                if r.get('_id') == rule_id:
                    rule = r
                    break

            if not rule:
                logger.error(f"Rule {rule_id} not found")
                return False

            # Update the enabled field
            rule['enabled'] = enabled

            # Send update request
            url = f"{self.base_url}{self.api_path}/{rule_id}"
            response = self.session.put(url, json=rule, timeout=10)

            if response.status_code == 200:
                action = "enabled" if enabled else "disabled"
                logger.info(f"Successfully {action} traffic rule {rule.get('description', rule_id)}")
                return True
            else:
                logger.error(f"Failed to update rule: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error updating rule: {e}")
            return False

    def get_rule_status(self, rule_id=None):
        """
        Get current status of traffic rule

        Args:
            rule_id: Rule ID to check (uses configured rule_id if not provided)

        Returns:
            True if enabled, False if disabled, None if error
        """
        if not rule_id:
            rule_id = self.firewall_rule_id

        if not rule_id:
            logger.error("No rule ID provided or configured")
            return None

        rules = self.get_traffic_rules()
        if not rules:
            return None

        for rule in rules:
            if rule.get('_id') == rule_id:
                return rule.get('enabled', False)

        logger.error(f"Rule {rule_id} not found")
        return None

    def initialize_rule_id(self):
        """
        Find and store the traffic rule ID by name
        Useful for first-time setup

        Returns:
            Rule ID if found, None otherwise
        """
        rule = self.find_rule_by_name(Config.FIREWALL_RULE_NAME)
        if rule:
            self.firewall_rule_id = rule.get('_id')
            logger.info(f"Initialized rule ID: {self.firewall_rule_id}")
            logger.info(f"Add this to your .env file: FIREWALL_RULE_ID={self.firewall_rule_id}")
            return self.firewall_rule_id
        return None


def test_unifi():
    """Test UniFi OS connection and rule management"""
    logger.info("Testing UniFi OS connection...")

    controller = UniFiController()

    # Verify API access
    if not controller.verify_access():
        logger.error("Failed to connect - check your API key in .env")
        return

    # Get all rules
    logger.info("\nFetching traffic rules...")
    rules = controller.get_traffic_rules()

    if rules:
        logger.info(f"Found {len(rules)} traffic rules:")
        for rule in rules:
            enabled = "✓" if rule.get('enabled') else "✗"
            logger.info(f"  [{enabled}] {rule.get('description')} (ID: {rule.get('_id')})")

    # Try to find the YouTube blocking rule
    logger.info(f"\nLooking for rule: {Config.FIREWALL_RULE_NAME}")
    rule = controller.find_rule_by_name(Config.FIREWALL_RULE_NAME)

    if rule:
        rule_id = rule.get('_id')
        logger.info(f"Found rule ID: {rule_id}")

        # Test enable/disable
        logger.info("\nTesting rule toggle...")
        current_status = rule.get('enabled')
        logger.info(f"Current status: {'Enabled' if current_status else 'Disabled'}")

        # Toggle it
        if current_status:
            logger.info("Disabling rule...")
            controller.disable_rule(rule_id)
        else:
            logger.info("Enabling rule...")
            controller.enable_rule(rule_id)

        # Check new status
        import time
        time.sleep(1)
        new_status = controller.get_rule_status(rule_id)
        logger.info(f"New status: {'Enabled' if new_status else 'Disabled'}")

        # Restore original state
        logger.info("Restoring original state...")
        if current_status:
            controller.enable_rule(rule_id)
        else:
            controller.disable_rule(rule_id)

        final_status = controller.get_rule_status(rule_id)
        logger.info(f"Restored status: {'Enabled' if final_status else 'Disabled'}")

    else:
        logger.warning(f"Rule '{Config.FIREWALL_RULE_NAME}' not found")
        logger.info("Please create this rule in UniFi Controller first")

    logger.info("\nTest complete")


if __name__ == "__main__":
    # Run test if executed directly
    test_unifi()
