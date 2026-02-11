"""
Optional web dashboard for monitoring cadence and YouTube block status
"""
from flask import Flask, render_template, jsonify
import threading
import time
from config import Config
from logger import setup_logger

logger = setup_logger('web_dashboard')

app = Flask(__name__)

# Shared state (will be updated by cadence monitor)
dashboard_state = {
    'current_cadence': 0,
    'average_cadence': 0,
    'threshold': Config.CADENCE_THRESHOLD,
    'youtube_blocked': False,
    'sensor_connected': False,
    'controller_connected': False,
    'last_update': time.time()
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
    dashboard_state.update({
        'current_cadence': cadence,
        'average_cadence': avg_cadence,
        'youtube_blocked': blocked,
        'sensor_connected': sensor_conn,
        'controller_connected': controller_conn,
        'last_update': time.time()
    })


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', config=Config)


@app.route('/api/status')
def status():
    """API endpoint for current status"""
    return jsonify(dashboard_state)


@app.route('/api/config')
def config():
    """API endpoint for configuration"""
    return jsonify({
        'threshold': Config.CADENCE_THRESHOLD,
        'grace_period': Config.GRACE_PERIOD_SECONDS,
        'rolling_window': Config.ROLLING_AVERAGE_WINDOW
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
