# Peloton Cadence YouTube Control

Monitor your Peloton bike's cadence via Bluetooth and automatically block/unblock YouTube access based on pedaling effort. Perfect for parents who want their kids to actually exercise while watching videos!

## How It Works

1. **Bluetooth cadence sensor** on Peloton pedals sends real-time RPM data
2. **Raspberry Pi** monitors cadence and calculates rolling average
3. When cadence drops below threshold → **UniFi firewall blocks YouTube**
4. When cadence rises above threshold → **YouTube access restored**

## Requirements

### Hardware
- Raspberry Pi 3/4/5 with built-in Bluetooth
- Bluetooth cadence sensor (installed on Peloton pedals)
- Ubiquiti UniFi network with Cloud Key or UDM

### Software
- Raspberry Pi OS (Lite recommended)
- Python 3.9+
- UniFi Controller with API access

## Installation

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip bluetooth bluez git

# Enable Bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Clone Repository

```bash
cd ~
git clone https://github.com/avidan/peloton-cadence-control.git
cd peloton-cadence-control
```

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Configure UniFi Firewall Rule

1. Log into your UniFi Controller
2. Go to **Settings → Firewall & Security → Create New Rule**
3. Configure the rule:
   - **Name**: `block_youtube_peloton`
   - **Action**: Drop
   - **Protocol**: TCP
   - **Source**: Your Peloton's IP address (assign static IP first!)
   - **Destination**: Port 443, 80
   - **Domain Names**:
     - `youtube.com`
     - `*.youtube.com`
     - `googlevideo.com`
     - `*.googlevideo.com`
     - `ytimg.com`
     - `*.ytimg.com`
   - **Initial State**: DISABLED
4. Save the rule

### 5. Configure Application

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings:**
```bash
# UniFi credentials
UNIFI_HOST=192.168.1.1
UNIFI_USERNAME=your_admin_user
UNIFI_PASSWORD=your_password

# Peloton IP (assign static IP in UniFi first!)
PELOTON_IP=192.168.1.100

# Firewall rule name (must match the rule you created)
FIREWALL_RULE_NAME=block_youtube_peloton

# Cadence threshold (RPM)
CADENCE_THRESHOLD=60
```

## First Time Setup

### Find Your Cadence Sensor

```bash
# Scan for Bluetooth devices
python3 ble_reader.py
```

This will show all nearby BLE devices. Find your cadence sensor and note its MAC address.

Add it to `.env`:
```bash
CADENCE_SENSOR_MAC=AA:BB:CC:DD:EE:FF
```

### Test UniFi Connection

```bash
# Test UniFi API connection
python3 unifi_controller.py
```

This will:
- Connect to your UniFi Controller
- List all firewall rules
- Find your YouTube blocking rule
- Test enable/disable functionality

The script will display the firewall rule ID. Add it to `.env`:
```bash
FIREWALL_RULE_ID=abc123def456
```

### Test Complete System

```bash
# Run the main monitor
python3 cadence_monitor.py
```

Start pedaling and watch the logs. You should see:
- Cadence readings from the sensor
- Average cadence calculations
- YouTube blocking/unblocking based on threshold

Press `Ctrl+C` to stop.

## Production Deployment

### Install as System Service

```bash
# Copy service file
sudo cp peloton-cadence.service /etc/systemd/system/

# Edit service file if your paths differ
sudo nano /etc/systemd/system/peloton-cadence.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable peloton-cadence

# Start service
sudo systemctl start peloton-cadence

# Check status
sudo systemctl status peloton-cadence
```

### View Logs

```bash
# Follow live logs
sudo journalctl -u peloton-cadence -f

# View recent logs
sudo journalctl -u peloton-cadence -n 100
```

### Stop/Restart Service

```bash
# Stop
sudo systemctl stop peloton-cadence

# Restart
sudo systemctl restart peloton-cadence

# Disable (prevent auto-start on boot)
sudo systemctl disable peloton-cadence
```

## Configuration Reference

### Cadence Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `CADENCE_THRESHOLD` | 60 | Minimum RPM to allow YouTube (50-70 recommended) |
| `GRACE_PERIOD_SECONDS` | 3 | Delay before state changes to prevent flickering |
| `ROLLING_AVERAGE_WINDOW` | 5 | Seconds of data to average for smoother readings |

### Thresholds Guide

- **50 RPM**: Easy, conversational pace
- **60 RPM**: Moderate effort (recommended)
- **70 RPM**: Higher intensity
- **80+ RPM**: Vigorous effort

## Troubleshooting

### "Failed to connect to cadence sensor"

1. Check sensor battery
2. Make sure sensor isn't paired with another device (Peloton app, phone)
3. Verify Bluetooth is enabled: `sudo systemctl status bluetooth`
4. Try manual scan: `python3 ble_reader.py`

### "Failed to connect to UniFi Controller"

1. Verify credentials in `.env`
2. Check UniFi Controller is accessible: `ping 192.168.1.1`
3. Ensure API access is enabled in UniFi settings
4. Check firewall isn't blocking port 8443

### "Could not find firewall rule"

1. Verify rule name matches exactly (case-sensitive)
2. Check rule exists in UniFi Controller
3. Manually specify `FIREWALL_RULE_ID` in `.env`

### YouTube still works when not pedaling

1. Check Peloton has correct static IP
2. Verify firewall rule targets correct IP/MAC
3. Test rule manually in UniFi Controller
4. Check DNS isn't being bypassed (Peloton might use DoH)

### Cadence readings seem wrong

1. Verify sensor is properly installed
2. Check sensor is compatible with CSC standard
3. Try different sensor if available
4. Enable debug logging: `LOG_LEVEL=DEBUG`

## Advanced Features

### Custom Thresholds for Different Kids

Edit `.env` to create profiles:
```bash
# Morning (easier)
CADENCE_THRESHOLD_MORNING=50

# After school (moderate)
CADENCE_THRESHOLD_AFTERNOON=60

# Weekend (harder)
CADENCE_THRESHOLD_WEEKEND=70
```

Then modify `cadence_monitor.py` to switch based on time of day.

### Block Other Apps

Add more domains to your UniFi firewall rule:
- TikTok: `tiktok.com`, `*.tiktok.com`
- Netflix: `netflix.com`, `*.netflix.com`
- Instagram: `instagram.com`, `*.instagram.com`

### Web Dashboard (Optional)

Access real-time monitoring at `http://<raspberry-pi-ip>:5000`

Enable in `.env`:
```bash
WEB_DASHBOARD_ENABLED=true
WEB_DASHBOARD_PORT=5000
```

## Project Structure

```
peloton-cadence-control/
├── cadence_monitor.py       # Main control loop
├── ble_reader.py             # Bluetooth LE sensor interface
├── unifi_controller.py       # UniFi API client
├── config.py                 # Configuration management
├── logger.py                 # Logging setup
├── web_dashboard.py          # Optional Flask web UI
├── requirements.txt          # Python dependencies
├── peloton-cadence.service   # systemd service file
├── .env.example              # Example configuration
└── README.md                 # This file
```

## Security Notes

1. **Never commit `.env` file** - it contains passwords
2. Use a dedicated UniFi API user with minimal permissions
3. The `.env` file should be readable only by the pi user:
   ```bash
   chmod 600 .env
   ```

## Contributing

Found a bug? Have an improvement? Open an issue or pull request!

## License

MIT License - use freely, at your own risk

## Credits

Created by a frustrated parent who wanted their kids to actually exercise 🚴‍♂️

---

**Note**: This is a parenting tool using network-level blocking. Determined kids might find workarounds (VPN, cellular data, etc.). The real goal is teaching healthy habits, not creating an unbreakable system!
