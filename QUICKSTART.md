# Quick Start Guide

Get up and running in 15 minutes!

## Prerequisites Checklist

- [ ] Raspberry Pi 3/4/5 with Raspberry Pi OS installed
- [ ] Bluetooth cadence sensor installed on Peloton pedals
- [ ] Ubiquiti UniFi network with Cloud Key or UDM
- [ ] Peloton tablet connected to your network

## Step 1: Network Setup (5 minutes)

### Assign Static IP to Peloton

1. Log into UniFi Controller
2. Go to **Clients** → Find your Peloton tablet
3. Click **Settings** → **Network** → **Fixed IP Address**
4. Assign an IP (e.g., `192.168.1.100`)
5. Note the MAC address

### Create Firewall Rule

1. Go to **Settings** → **Firewall & Security**
2. Click **Create New Rule**
3. Configure:
   ```
   Name: block_youtube_peloton
   Action: Drop
   Protocol: TCP
   Source: <Peloton IP>
   Port: 443, 80
   Domains: youtube.com, *.youtube.com, googlevideo.com, *.googlevideo.com
   State: DISABLED
   ```
4. Save

## Step 2: Raspberry Pi Setup (5 minutes)

### Install on Raspberry Pi

```bash
cd ~
git clone https://github.com/avidan/peloton-cadence-control.git
cd peloton-cadence-control
./setup.sh
```

The setup script will:
- Update system packages
- Install dependencies
- Enable Bluetooth
- Create `.env` configuration file

### Configure Settings

Edit `.env`:

```bash
nano .env
```

**Minimum required settings:**

```bash
# UniFi Controller
UNIFI_HOST=192.168.1.1
UNIFI_USERNAME=your_admin_username
UNIFI_PASSWORD=your_password

# Peloton
PELOTON_IP=192.168.1.100

# Firewall Rule
FIREWALL_RULE_NAME=block_youtube_peloton

# Cadence
CADENCE_THRESHOLD=60
```

Save: `Ctrl+O`, Enter, `Ctrl+X`

## Step 3: Initial Testing (5 minutes)

### Find Cadence Sensor

```bash
python3 ble_reader.py
```

Output will show:
```
Found device: Wahoo CADENCE (AA:BB:CC:DD:EE:FF)
```

Add MAC address to `.env`:
```bash
CADENCE_SENSOR_MAC=AA:BB:CC:DD:EE:FF
```

### Test UniFi Connection

```bash
python3 unifi_controller.py
```

Should show:
```
✓ Successfully logged in
Found rule 'block_youtube_peloton': abc123...
```

Copy the rule ID to `.env`:
```bash
FIREWALL_RULE_ID=abc123def456
```

### Test Complete System

```bash
python3 cadence_monitor.py
```

Expected output:
```
✓ Connected to cadence sensor
✓ Connected to UniFi Controller
Monitoring cadence... Threshold: 60 RPM
Cadence: 0 RPM | Avg: 0.0 RPM | YouTube=BLOCKED
```

**Test it:**
- Don't pedal → YouTube should be blocked
- Pedal above 60 RPM → YouTube should be allowed
- Stop pedaling → YouTube should block again

Press `Ctrl+C` to stop.

## Step 4: Deploy as Service

### Install Service

```bash
sudo cp peloton-cadence.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable peloton-cadence
sudo systemctl start peloton-cadence
```

### Check Status

```bash
sudo systemctl status peloton-cadence
```

Should show: **Active: active (running)**

### View Live Logs

```bash
sudo journalctl -u peloton-cadence -f
```

## Done!

Your system is now running 24/7. The service will:
- Auto-start on boot
- Automatically reconnect if connections drop
- Log all events

## Accessing Web Dashboard

If enabled, visit: `http://<raspberry-pi-ip>:5000`

To find your Raspberry Pi IP:
```bash
hostname -I
```

## Troubleshooting

### Cadence sensor not found?
- Check sensor battery
- Make sure sensor isn't connected to another device
- Try moving Raspberry Pi closer to bike

### UniFi connection failed?
- Verify credentials in `.env`
- Check `UNIFI_HOST` IP address
- Ensure API access is enabled in UniFi

### YouTube still works when not pedaling?
- Verify Peloton has correct static IP
- Check firewall rule is enabled in UniFi
- Test rule manually in UniFi Controller

## Next Steps

- Adjust `CADENCE_THRESHOLD` in `.env` to find right difficulty
- Set up web dashboard monitoring
- Add more blocked domains (TikTok, Netflix, etc.)
- Create time-based rules for different schedules

See `README.md` for full documentation.

---

**Happy exercising!** 🚴‍♂️
