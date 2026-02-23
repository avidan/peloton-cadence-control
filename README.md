# Peloton Cadence Control

Automatically block or allow YouTube access based on real-time pedaling cadence from a Bluetooth sensor on a Peloton bike. If the rider stops pedaling, YouTube gets blocked at the network level via UniFi firewall rules. Start pedaling again and it comes right back.

Built for parents who want their kids to actually exercise while watching videos.

## Architecture

```
┌──────────────────┐     BLE      ┌──────────────────┐    UniFi API    ┌──────────────┐
│  Cadence Sensor  │─────────────>│   Raspberry Pi   │───────────────>│ UniFi Gateway │
│  (on pedals)     │  CSC Profile │                  │  Enable/Disable│ (UDM/UDR/UCG) │
└──────────────────┘              │  cadence_monitor  │  Firewall Rule └──────────────┘
                                  │  web_dashboard    │                       │
                                  └────────┬─────────┘                       │
                                           │ :5000                    ┌──────┴──────┐
                                      ┌────┴────┐                    │   Peloton   │
                                      │ Browser │                    │  (YouTube)  │
                                      └─────────┘                    └─────────────┘
```

## Prerequisites

### Hardware
- **Raspberry Pi** 3/4/5 with built-in Bluetooth
- **Bluetooth cadence sensor** (any ANT+/BLE CSC-compatible sensor, mounted on Peloton pedals)
- **Ubiquiti UniFi gateway** (UDM, UDM Pro, UDR, or Cloud Gateway) running UniFi OS

### Software
- Raspberry Pi OS (Lite is sufficient)
- Python 3.9+
- Bluetooth enabled (`sudo systemctl enable bluetooth`)

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/avidan/peloton-cadence-control.git
cd peloton-cadence-control

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Create your config
cp .env.example .env
nano .env   # Set UNIFI_API_KEY and PELOTON_IP at minimum

# 4. Create the firewall rule in UniFi (see below)

# 5. Run it
python3 cadence_monitor.py
```

## Detailed Installation

### 1. Prepare the Raspberry Pi

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip bluetooth bluez git
sudo systemctl enable bluetooth && sudo systemctl start bluetooth
```

### 2. Clone and Install

```bash
cd ~
git clone https://github.com/avidan/peloton-cadence-control.git
cd peloton-cadence-control
pip3 install -r requirements.txt
```

### 3. Create a UniFi API Key

1. Log into your UniFi OS console (e.g. `https://192.168.1.1`)
2. Go to **Settings > Admins & Users > API Keys** (or your profile > API Keys)
3. Create a new API key with appropriate permissions
4. Copy the key for the next step

### 4. Create the Firewall Rule

In UniFi Network:
1. Go to **Settings > Firewall & Security > Create New Rule**
2. Configure:
   - **Name**: `block_youtube_peloton`
   - **Action**: Drop
   - **Source**: Your Peloton's IP address (assign a static IP first)
   - **Destination Domains**: `youtube.com`, `*.youtube.com`, `googlevideo.com`, `*.googlevideo.com`, `ytimg.com`, `*.ytimg.com`
   - **Initial State**: Disabled
3. Save the rule

### 5. Configure the Application

```bash
cp .env.example .env
nano .env
```

Set at minimum:
```bash
UNIFI_API_KEY=your_api_key_here
PELOTON_IP=192.168.1.100
```

### 6. Find Your Cadence Sensor

```bash
python3 ble_reader.py
```

Note the MAC address and add it to `.env`:
```bash
CADENCE_SENSOR_MAC=AA:BB:CC:DD:EE:FF
```

### 7. Test

```bash
python3 cadence_monitor.py
```

Start pedaling. You should see cadence readings and YouTube blocking/unblocking in the logs.

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `CADENCE_THRESHOLD` | `60` | Minimum RPM to allow YouTube access |
| `GRACE_PERIOD_SECONDS` | `3` | Seconds to wait before toggling firewall state |
| `ROLLING_AVERAGE_WINDOW` | `5` | Seconds of cadence data to average |
| `CADENCE_SENSOR_MAC` | *(empty)* | BLE MAC of cadence sensor (auto-scans if empty) |
| `CADENCE_SENSOR_NAME` | `Cadence` | BLE device name filter for scanning |
| `BLE_SCAN_TIMEOUT` | `10` | Seconds to scan for BLE devices |
| `UNIFI_HOST` | `192.168.1.1` | UniFi gateway IP/hostname |
| `UNIFI_PORT` | `443` | UniFi gateway HTTPS port |
| `UNIFI_API_KEY` | *(required)* | UniFi OS API key |
| `UNIFI_SITE` | `default` | UniFi site name |
| `UNIFI_VERIFY_SSL` | `false` | Verify SSL certificate |
| `PELOTON_IP` | `192.168.1.100` | Peloton bike's static IP |
| `FIREWALL_RULE_ID` | *(auto)* | Firewall rule ID (looked up by name if empty) |
| `FIREWALL_RULE_NAME` | `block_youtube_peloton` | Name of the firewall rule to control |
| `WEB_DASHBOARD_ENABLED` | `true` | Enable the web monitoring dashboard |
| `WEB_DASHBOARD_PORT` | `5000` | Dashboard HTTP port |
| `WEB_DASHBOARD_HOST` | `0.0.0.0` | Dashboard bind address |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | `peloton_cadence.log` | Log file path |

### Cadence Threshold Guide

| RPM | Effort Level |
|-----|-------------|
| 50 | Easy / conversational pace |
| 60 | Moderate effort (recommended default) |
| 70 | Brisk pace |
| 80+ | Vigorous effort |

## Web Dashboard

When enabled (default), a real-time monitoring dashboard is available at `http://<pi-ip>:5000`.

Features:
- **SVG cadence gauge** with color-coded arc (green/yellow/red based on threshold)
- **YouTube status** with animated glow indicator
- **Average cadence** with visual threshold bar
- **Live chart** showing the last 5 minutes of cadence history with threshold line
- **Session stats** including peak cadence and % time above threshold
- **System status** showing sensor and controller connection state
- Responsive design for mobile and desktop

The dashboard launches automatically with `cadence_monitor.py`. To test it standalone:
```bash
python3 web_dashboard.py
```

## Production Deployment

### Install as a systemd Service

```bash
sudo cp peloton-cadence.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable peloton-cadence
sudo systemctl start peloton-cadence
```

### Manage the Service

```bash
sudo systemctl status peloton-cadence    # Check status
sudo journalctl -u peloton-cadence -f    # Follow logs
sudo systemctl restart peloton-cadence   # Restart
sudo systemctl stop peloton-cadence      # Stop
```

## Troubleshooting

### Cannot connect to cadence sensor
- Check sensor battery
- Ensure sensor is not paired to another device (phone, Peloton app)
- Verify Bluetooth is running: `sudo systemctl status bluetooth`
- Scan manually: `python3 ble_reader.py`

### Cannot connect to UniFi controller
- Verify `UNIFI_API_KEY` in `.env` is correct
- Check the gateway is reachable: `ping 192.168.1.1`
- Ensure the API key has sufficient permissions
- Try `curl -k -H "X-API-Key: YOUR_KEY" https://192.168.1.1/proxy/network/v2/api/site/default/trafficrules`

### Firewall rule not found
- Verify `FIREWALL_RULE_NAME` matches exactly (case-sensitive)
- Check the rule exists in UniFi Network settings
- Set `FIREWALL_RULE_ID` explicitly if name lookup fails

### YouTube still works when cadence is low
- Confirm the Peloton has the correct static IP
- Verify the firewall rule targets the right IP
- Test the rule manually in UniFi (enable it and check if YouTube is blocked)
- The Peloton may use DNS-over-HTTPS; add DoH server IPs to the block list if needed

### Cadence readings seem wrong
- Ensure the sensor is properly mounted on the pedal crank
- Verify the sensor supports the Bluetooth CSC (Cycling Speed and Cadence) profile
- Try `LOG_LEVEL=DEBUG` for detailed BLE data

## Security Notes

- **Never commit `.env`** - it contains your API key. The `.gitignore` already excludes it.
- Use an API key with minimal permissions (read/write traffic rules only).
- The web dashboard has no authentication. Bind to `127.0.0.1` or use a reverse proxy if the Pi is on an untrusted network.
- Restrict `.env` file permissions: `chmod 600 .env`

## Project Structure

```
peloton-cadence-control/
├── cadence_monitor.py         # Main control loop
├── ble_reader.py              # Bluetooth LE sensor interface
├── unifi_controller.py        # UniFi OS API client
├── config.py                  # Configuration from .env
├── logger.py                  # Logging setup
├── web_dashboard.py           # Flask web dashboard + API
├── templates/
│   └── index.html             # Dashboard UI
├── static/
│   ├── app.js                 # Dashboard JavaScript (Chart.js, gauge, polling)
│   ├── style.css              # Dark-themed responsive styles
│   └── chart.min.js           # Bundled Chart.js v4 (no CDN needed)
├── requirements.txt           # Python dependencies
├── peloton-cadence.service    # systemd service file
├── .env.example               # Example configuration
└── README.md
```

## License

MIT License - use freely, at your own risk.
