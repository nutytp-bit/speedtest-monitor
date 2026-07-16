import os
import csv
import subprocess
from datetime import datetime
from pathlib import Path
import logging
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Database file
DB_FILE = "speedtest_results.csv"
PORT = int(os.getenv("PORT", 8000))

# Ensure CSV headers exist
def init_database():
    if not Path(DB_FILE).exists():
        with open(DB_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'download_mbps', 'upload_mbps', 'ping_ms', 'server'])
        logger.info("✅ Database initialized")

# Run speedtest using subprocess
def run_speedtest():
    try:
        logger.info("🚀 Starting speedtest...")

        # Run speedtest-cli command
        result = subprocess.run(
            ['speedtest-cli', '--simple'],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            logger.error(f"❌ Speedtest failed: {result.stderr}")
            return

        # Parse output: download,upload,ping
        lines = result.stdout.strip().split('\n')
        if len(lines) < 3:
            logger.error(f"❌ Invalid speedtest output: {result.stdout}")
            return

        timestamp = datetime.utcnow().isoformat() + "Z"
        download = round(float(lines[0]), 2)
        upload = round(float(lines[1]), 2)
        ping = round(float(lines[2]), 2)
        server = "Speedtest"

        # Save to CSV
        with open(DB_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, download, upload, ping, server])

        logger.info(f"✅ Test completed | Download: {download} Mbps | Upload: {upload} Mbps | Ping: {ping} ms")

    except subprocess.TimeoutExpired:
        logger.error("❌ Speedtest timeout (took too long)")
    except FileNotFoundError:
        logger.error("❌ speedtest-cli not found. Try: pip install speedtest-cli")
    except Exception as e:
        logger.error(f"❌ Speedtest error: {str(e)}")

# API Endpoints
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/latest', methods=['GET'])
def get_latest():
    """Get latest speedtest result"""
    try:
        if not Path(DB_FILE).exists():
            return jsonify({"error": "No data yet", "message": "Waiting for first speedtest to complete (1-2 minutes)"}), 404

        with open(DB_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                return jsonify({"error": "No data yet", "message": "Speedtest still running or failed"}), 404

            last_line = lines[-1].strip().split(',')
            return jsonify({
                "timestamp": last_line[0],
                "download_mbps": float(last_line[1]),
                "upload_mbps": float(last_line[2]),
                "ping_ms": float(last_line[3]),
                "server": last_line[4]
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics from all tests"""
    try:
        if not Path(DB_FILE).exists():
            return jsonify({"error": "No data yet"}), 404

        with open(DB_FILE, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)

            if not data:
                return jsonify({"error": "No data yet"}), 404

            downloads = [float(row['download_mbps']) for row in data]
            uploads = [float(row['upload_mbps']) for row in data]
            pings = [float(row['ping_ms']) for row in data]

            return jsonify({
                "total_tests": len(data),
                "download": {
                    "avg": round(sum(downloads) / len(downloads), 2),
                    "max": round(max(downloads), 2),
                    "min": round(min(downloads), 2)
                },
                "upload": {
                    "avg": round(sum(uploads) / len(uploads), 2),
                    "max": round(max(uploads), 2),
                    "min": round(min(uploads), 2)
                },
                "ping": {
                    "avg": round(sum(pings) / len(pings), 2),
                    "max": round(max(pings), 2),
                    "min": round(min(pings), 2)
                }
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get all speedtest history"""
    try:
        if not Path(DB_FILE).exists():
            return jsonify({"error": "No data yet"}), 404

        with open(DB_FILE, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)

            if not data:
                return jsonify({"error": "No data yet"}), 404

            # Convert strings to numbers
            for row in data:
                row['download_mbps'] = float(row['download_mbps'])
                row['upload_mbps'] = float(row['upload_mbps'])
                row['ping_ms'] = float(row['ping_ms'])

            return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Schedule speedtest to run every hour
def start_scheduler():
    scheduler = BackgroundScheduler()

    # Run every hour
    scheduler.add_job(
        func=run_speedtest,
        trigger="interval",
        hours=1,
        id='speedtest_job',
        name='Speedtest every hour',
        replace_existing=True
    )

    # Also run immediately on startup (with delay to let app stabilize)
    scheduler.add_job(
        func=run_speedtest,
        trigger="date",
        run_date=datetime.now(),
        id='speedtest_startup',
        name='Initial speedtest'
    )

    scheduler.start()
    logger.info("✅ Scheduler started - speedtest will run every hour + now")

if __name__ == '__main__':
    # Initialize database
    init_database()

    # Start scheduler
    start_scheduler()

    # Run Flask app
    logger.info(f"🚀 Starting app on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
