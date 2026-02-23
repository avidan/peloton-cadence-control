"""
Web dashboard for monitoring cadence and YouTube block status
"""
from flask import Flask, render_template, jsonify, request
from collections import deque
import threading
import time
from config import Config
from logger import setup_logger

logger = setup_logger('web_dashboard')

app = Flask(__name__)

# Cadence history for charting (5 minutes at 1 reading/sec)
cadence_history = deque(maxlen=300)

# Shared state (updated by cadence monitor)
dashboard_state = {
    'current_cadence': 0,
    'average_cadence': 0,
    'threshold': Config.CADENCE_THRESHOLD,
    'grace_period': Config.GRACE_PERIOD_SECONDS,
    'rolling_window': Config.ROLLING_AVERAGE_WINDOW,
    'youtube_blocked': False,
    'sensor_connected': False,
    'controller_connected': False,
    'last_update': time.time(),
    'session_start': time.time(),
    'peak_cadence': 0,
    'time_above_threshold': 0,
    'total_readings': 0,
}


def update_state(cadence, avg_cadence, blocked, sensor_conn, controller_conn):
    """
    Update dashboard state from main monitor

    Args:
        cadence: Current cadence reading
        avg_cadence: Rolling average cadence
        blocked: YouTube block status
        sensor_conn: Sensor connection status
        controller_conn: Controller connection status
    """
    global dashboard_state
    now = time.time()

    # Track history
    cadence_history.append({
        'time': now,
        'cadence': cadence,
    })

    # Update session stats
    dashboard_state['total_readings'] += 1
    if cadence > dashboard_state['peak_cadence']:
        dashboard_state['peak_cadence'] = cadence
    if cadence >= Config.CADENCE_THRESHOLD:
        dashboard_state['time_above_threshold'] += 1

    dashboard_state.update({
        'current_cadence': cadence,
        'average_cadence': avg_cadence,
        'youtube_blocked': blocked,
        'sensor_connected': sensor_conn,
        'controller_connected': controller_conn,
        'last_update': now,
    })


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', config=Config)


@app.route('/api/status')
def status():
    """API endpoint for current status"""
    state = dict(dashboard_state)
    total = state['total_readings']
    if total > 0:
        state['percent_above_threshold'] = round(
            state['time_above_threshold'] / total * 100, 1
        )
    else:
        state['percent_above_threshold'] = 0
    return jsonify(state)


@app.route('/api/history')
def history():
    """API endpoint for cadence history (chart data)"""
    now = time.time()
    points = [
        {'t': round(entry['time'] - now, 1), 'c': entry['cadence']}
        for entry in cadence_history
    ]
    return jsonify({
        'points': points,
        'threshold': Config.CADENCE_THRESHOLD,
    })


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """API endpoint for configuration (GET to read, POST to update)"""
    if request.method == 'GET':
        return jsonify({
            'threshold': Config.CADENCE_THRESHOLD,
            'grace_period': Config.GRACE_PERIOD_SECONDS,
            'rolling_window': Config.ROLLING_AVERAGE_WINDOW,
        })

    # POST — update one or more config values
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    # Validation rules: (field, config attr, min, max, unit)
    fields = {
        'threshold':     ('CADENCE_THRESHOLD',      1,  200, 'RPM'),
        'grace_period':  ('GRACE_PERIOD_SECONDS',   1,   60, 's'),
        'rolling_window': ('ROLLING_AVERAGE_WINDOW', 1,   60, 's'),
    }

    updated = {}
    for key, (attr, lo, hi, unit) in fields.items():
        if key not in data:
            continue
        try:
            value = int(data[key])
        except (TypeError, ValueError):
            return jsonify({'error': f'{key} must be an integer'}), 400
        if not lo <= value <= hi:
            return jsonify({'error': f'{key} must be between {lo} and {hi}'}), 400
        setattr(Config, attr, value)
        updated[key] = value
        logger.info(f"Config {attr} updated to {value}{unit} via web UI")

    if not updated:
        return jsonify({'error': 'No valid fields provided'}), 400

    # Keep dashboard_state in sync
    if 'threshold' in updated:
        dashboard_state['threshold'] = updated['threshold']
    if 'grace_period' in updated:
        dashboard_state['grace_period'] = updated['grace_period']
    if 'rolling_window' in updated:
        dashboard_state['rolling_window'] = updated['rolling_window']

    return jsonify({
        'threshold': Config.CADENCE_THRESHOLD,
        'grace_period': Config.GRACE_PERIOD_SECONDS,
        'rolling_window': Config.ROLLING_AVERAGE_WINDOW,
    })


def run_dashboard():
    """Run Flask dashboard in background thread"""
    if not Config.WEB_DASHBOARD_ENABLED:
        logger.info("Web dashboard is disabled")
        return

    logger.info(f"Starting web dashboard on {Config.WEB_DASHBOARD_HOST}:{Config.WEB_DASHBOARD_PORT}")
    app.run(
        host=Config.WEB_DASHBOARD_HOST,
        port=Config.WEB_DASHBOARD_PORT,
        debug=False,
        use_reloader=False
    )


def start_dashboard_thread():
    """Start dashboard in a separate thread"""
    if not Config.WEB_DASHBOARD_ENABLED:
        return None

    thread = threading.Thread(target=run_dashboard, daemon=True)
    thread.start()
    logger.info(f"Dashboard available at http://localhost:{Config.WEB_DASHBOARD_PORT}")
    return thread


if __name__ == "__main__":
    run_dashboard()
