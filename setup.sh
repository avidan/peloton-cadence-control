#!/bin/bash
# Peloton Cadence Control - Setup Script for Raspberry Pi

set -e  # Exit on error

echo "========================================="
echo "Peloton Cadence Control - Setup"
echo "========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠ Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3-pip bluetooth bluez git

# Enable Bluetooth
echo "📡 Enabling Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env configuration file..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your settings:"
    echo "   - UniFi credentials"
    echo "   - Peloton IP address"
    echo "   - Cadence threshold"
    echo ""
    read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit later..."
    nano .env
else
    echo "✓ .env file already exists"
fi

# Make Python files executable
chmod +x cadence_monitor.py
chmod +x ble_reader.py
chmod +x unifi_controller.py

echo ""
echo "========================================="
echo "✓ Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure UniFi firewall rule:"
echo "   - Log into UniFi Controller"
echo "   - Create firewall rule to block YouTube for Peloton"
echo "   - See README.md for detailed instructions"
echo ""
echo "2. Find your cadence sensor:"
echo "   python3 ble_reader.py"
echo ""
echo "3. Test UniFi connection:"
echo "   python3 unifi_controller.py"
echo ""
echo "4. Run the monitor:"
echo "   python3 cadence_monitor.py"
echo ""
echo "5. Install as a service (optional):"
echo "   sudo cp peloton-cadence.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable peloton-cadence"
echo "   sudo systemctl start peloton-cadence"
echo ""
echo "For detailed documentation, see README.md"
echo ""
