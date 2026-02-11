# Peloton Cadence YouTube Control - Project Summary

## Overview

A complete IoT automation system that monitors real-time cadence from a Bluetooth sensor on your Peloton bike and dynamically controls YouTube access via your Ubiquiti network firewall. When kids stop pedaling hard enough, YouTube gets blocked. When they pedal above the threshold, YouTube access is restored.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  BLE Cadence    │         │  Raspberry Pi    │         │ UniFi Cloud Key │
│  Sensor         │ ──BLE──>│  Controller      │ ──API──>│ Firewall Rules  │
│  (on pedals)    │         │  (Python)        │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │                            │
                                      │                            │
                                      v                            v
                            ┌──────────────────┐         ┌─────────────────┐
                            │  Web Dashboard   │         │  Peloton Tablet │
                            │  (Optional)      │         │  (YouTube)      │
                            └──────────────────┘         └─────────────────┘
```

## Components Built

### 1. **Core Modules** (Python)

#### `cadence_monitor.py` - Main Control Loop
- Orchestrates all components
- Implements control logic with rolling average
- Manages state changes with grace period
- Handles reconnection logic
- Can run as systemd service

#### `ble_reader.py` - Bluetooth LE Interface
- Scans for cadence sensors
- Connects via Bluetooth Low Energy (BLE)
- Parses CSC (Cycling Speed and Cadence) protocol
- Provides real-time cadence readings
- Auto-reconnects on connection loss

#### `unifi_controller.py` - UniFi API Client
- Authenticates with UniFi Controller
- Manages firewall rules via REST API
- Enables/disables YouTube blocking rule
- Handles session management

#### `config.py` - Configuration Management
- Loads settings from `.env` file
- Validates required configuration
- Provides configuration display
- Type-safe configuration access

#### `logger.py` - Logging Setup
- Configurable log levels
- Console and file output
- Structured logging format
- Timestamp and function tracking

### 2. **Web Dashboard** (Optional)

#### `web_dashboard.py` - Flask Web Server
- Real-time status monitoring
- RESTful API endpoints
- Runs in background thread
- Configurable port and host

#### `templates/index.html` - Dashboard UI
- Real-time cadence display
- YouTube block status indicator
- Connection health monitoring
- Configuration display

#### `static/style.css` - Dashboard Styling
- Modern, responsive design
- Color-coded status indicators
- Gradient background
- Mobile-friendly layout

#### `static/app.js` - Dashboard Logic
- Auto-refreshing data (1s interval)
- Status animations
- Time-ago calculations
- Connection status updates

### 3. **Deployment Files**

#### `.env.example` - Configuration Template
- All configuration options documented
- Secure defaults
- Clear instructions

#### `requirements.txt` - Python Dependencies
```
bleak>=0.21.0          # Bluetooth LE
requests>=2.31.0       # HTTP requests
python-dotenv>=1.0.0   # Config management
flask>=3.0.0           # Web dashboard
urllib3>=2.0.0         # SSL handling
```

#### `peloton-cadence.service` - Systemd Service
- Auto-start on boot
- Automatic restart on failure
- Logging to journald
- Security hardening

#### `setup.sh` - Installation Script
- One-command setup
- System package installation
- Python dependency installation
- Bluetooth configuration
- Interactive `.env` setup

### 4. **Documentation**

#### `README.md` - Complete Documentation
- Detailed installation instructions
- Configuration reference
- Troubleshooting guide
- Advanced features
- Security notes

#### `QUICKSTART.md` - Rapid Deployment Guide
- 15-minute setup walkthrough
- Step-by-step checklist
- Common issues and fixes
- Testing procedures

#### `.gitignore` - Git Configuration
- Excludes sensitive `.env` file
- Python build artifacts
- IDE files
- Log files

## Key Features

### Real-Time Monitoring
- Reads cadence every second
- 5-second rolling average for smooth readings
- Immediate blocking when cadence drops

### Intelligent Control Logic
- Configurable RPM threshold
- Grace period prevents flickering
- Hysteresis for stable state changes
- Fail-safe defaults (blocked if sensor disconnects for safety)

### Robust Error Handling
- Auto-reconnect to Bluetooth sensor
- Resilient to API failures
- Graceful degradation
- Comprehensive logging

### Production Ready
- Systemd service integration
- Auto-start on boot
- Watchdog for crash recovery
- Secure defaults

### User-Friendly
- Web dashboard for monitoring
- Simple configuration via `.env` file
- Automated setup script
- Extensive documentation

## Configuration Options

### Cadence Settings
- **CADENCE_THRESHOLD**: RPM threshold (default: 60)
- **GRACE_PERIOD_SECONDS**: State change delay (default: 3)
- **ROLLING_AVERAGE_WINDOW**: Smoothing window (default: 5)

### Bluetooth Settings
- **CADENCE_SENSOR_MAC**: Specific sensor address
- **CADENCE_SENSOR_NAME**: Search by name
- **BLE_SCAN_TIMEOUT**: Scan duration

### Network Settings
- **UNIFI_HOST**: Controller IP address
- **UNIFI_PORT**: API port (default: 8443)
- **UNIFI_USERNAME**: API credentials
- **UNIFI_PASSWORD**: API credentials
- **PELOTON_IP**: Target device IP
- **FIREWALL_RULE_ID**: Rule identifier

### Dashboard Settings
- **WEB_DASHBOARD_ENABLED**: Enable/disable UI
- **WEB_DASHBOARD_PORT**: HTTP port (default: 5000)

## Technical Highlights

### Bluetooth Communication
- Uses standard CSC service (UUID: 0x1816)
- Parses CSC Measurement characteristic
- Handles uint16 rollover correctly
- Calculates RPM from crank revolutions

### UniFi API Integration
- RESTful API with session management
- Firewall rule manipulation
- Rule discovery by name
- SSL certificate handling

### Async/Await Pattern
- Python asyncio for concurrent operations
- Non-blocking BLE notifications
- Efficient resource usage
- Clean shutdown handling

### State Management
- Rolling window with deque
- Time-based grace period
- State change tracking
- Connection health monitoring

## Security Considerations

1. **Credential Protection**
   - `.env` file excluded from git
   - File permissions restricted
   - No hardcoded credentials

2. **Network Security**
   - Optional SSL verification
   - API user with minimal permissions
   - IP-based firewall targeting

3. **Service Security**
   - NoNewPrivileges in systemd
   - PrivateTmp isolation
   - Non-root execution

## Testing Strategy

### Unit Testing
- Individual module testing:
  - `python3 ble_reader.py` - Sensor connection
  - `python3 unifi_controller.py` - API interaction

### Integration Testing
- Complete system test:
  - `python3 cadence_monitor.py` - Full workflow

### Verification
- No pedaling → YouTube blocked
- Pedaling above threshold → YouTube allowed
- Connection loss → Graceful handling

## Deployment Options

### Development
```bash
python3 cadence_monitor.py
```

### Production (Systemd Service)
```bash
sudo systemctl enable peloton-cadence
sudo systemctl start peloton-cadence
```

### Monitoring
```bash
# Live logs
sudo journalctl -u peloton-cadence -f

# Web dashboard
http://<raspberry-pi-ip>:5000
```

## Future Enhancements

Potential additions (not implemented):
1. Multiple user profiles with different thresholds
2. Time-based rules (harder during homework time)
3. Gamification with rewards
4. Mobile app for remote control
5. Historical statistics and charts
6. Notification system for parents
7. Additional blocked services (TikTok, Netflix, etc.)

## Project Statistics

- **Lines of Code**: ~1,500+ across all modules
- **Files Created**: 17 files
- **Documentation**: 3 comprehensive guides
- **Configuration Options**: 20+ settings
- **Estimated Development Time**: 10-12 hours
- **Setup Time**: 15 minutes (with QUICKSTART guide)

## Testing Checklist

- [x] Bluetooth sensor discovery
- [x] BLE connection and notifications
- [x] CSC data parsing
- [x] UniFi API authentication
- [x] Firewall rule manipulation
- [x] Rolling average calculation
- [x] State change logic
- [x] Grace period implementation
- [x] Auto-reconnection
- [x] Logging system
- [x] Web dashboard
- [x] Systemd service
- [x] Setup script

## Credits

Created for a parent who wants their kids to actually exercise while using their Peloton! 🚴‍♂️

## License

MIT License - Use freely, at your own risk!
