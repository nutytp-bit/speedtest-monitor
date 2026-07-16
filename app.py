import os
import csv
import threading
from datetime import datetime
from pathlib import Path
import logging
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import speedtest

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger("speedtest-monitor")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
app = Flask(__name__)
DB_FILE = "speedtest_results.csv"
PORT = int(os.getenv("PORT", 8000))

# Prevent two speedtests running at the same time
_test_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def init_database():
    if not Path(DB_FILE).exists():
        with open(DB_FILE, 'w', newline='') as f:
            csv.writer(f).writerow(
                ['timestamp', 'download_mbps', 'upload_mbps', 'ping_ms', 'server']
            )
        logger.info("✅ Database created: %s", DB_FILE)
    else:
        logger.info("✅ Database exists: %s", DB_FILE)


# ---------------------------------------------------------------------------
# Speedtest
# ---------------------------------------------------------------------------
def run_speedtest():
    # If a test is already running, skip
    if not _test_lock.acquire(blocking=False):
        logger.info("⏭️  Speedtest already running, skipping")
        return {"error": "Speedtest already running"}

    try:
        logger.info("🚀 Starting speedtest...")
        st = speedtest.Speedtest(secure=True)

        logger.info("📍 Finding best server...")
        st.get_best_server()

        logger.info("⬇️  Testing download...")
        st.download()

        logger.info("⬆️  Testing upload...")
        st.upload()

        r = st.results.dict()
        row = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "download_mbps": round(r['download'] / 1_000_000, 2),
            "upload_mbps": round(r['upload'] / 1_000_000, 2),
            "ping_ms": round(r['ping'], 2),
            "server": r['server'].get('sponsor', 'Unknown'),
        }

        with open(DB_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([
                row["timestamp"], row["download_mbps"],
                row["upload_mbps"], row["ping_ms"], row["server"]
            ])

        logger.info(
            "✅ Done | DL: %s Mbps | UL: %s Mbps | Ping: %s ms | %s",
            row["download_mbps"], row["upload_mbps"],
            row["ping_ms"], row["server"]
        )
        return row

    except Exception as e:
        logger.error("❌ Speedtest failed: %s: %s", type(e).__name__, e)
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        _test_lock.release()


def _read_rows():
    if not Path(DB_FILE).exists():
        return []
    with open(DB_FILE, 'r') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    return jsonify({
        "app": "Internet Speedtest Monitor",
        "status": "running",
        "endpoints": {
            "/run": "Force a speedtest now (takes 30-60s)",
            "/latest": "Latest result",
            "/stats": "Statistics (avg/max/min)",
            "/history": "All records",
            "/health": "Health check"
        }
    }), 200


@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}), 200


@app.route('/run')
def force_run():
    """Force run a speedtest right now and return the result."""
    result = run_speedtest()
    if "error" in result:
        return jsonify(result), 500
    return jsonify({"message": "Speedtest completed", "result": result}), 200


@app.route('/latest')
def latest():
    rows = _read_rows()
    if not rows:
        return jsonify({"error": "No data yet", "hint": "Call /run to trigger a test"}), 404
    last = rows[-1]
    return jsonify({
        "timestamp": last["timestamp"],
        "download_mbps": float(last["download_mbps"]),
        "upload_mbps": float(last["upload_mbps"]),
        "ping_ms": float(last["ping_ms"]),
        "server": last["server"],
    }), 200


@app.route('/stats')
def stats():
    rows = _read_rows()
    if not rows:
        return jsonify({"error": "No data yet", "hint": "Call /run to trigger a test"}), 404

    dl = [float(r["download_mbps"]) for r in rows]
    ul = [float(r["upload_mbps"]) for r in rows]
    pg = [float(r["ping_ms"]) for r in rows]

    def summ(v):
        return {"avg": round(sum(v) / len(v), 2), "max": round(max(v), 2), "min": round(min(v), 2)}

    return jsonify({
        "total_tests": len(rows),
        "last_updated": rows[-1]["timestamp"],
        "download": summ(dl),
        "upload": summ(ul),
        "ping": summ(pg),
    }), 200


@app.route('/history')
def history():
    rows = _read_rows()
    if not rows:
        return jsonify({"error": "No data yet", "hint": "Call /run to trigger a test"}), 404
    for r in rows:
        r["download_mbps"] = float(r["download_mbps"])
        r["upload_mbps"] = float(r["upload_mbps"])
        r["ping_ms"] = float(r["ping_ms"])
    return jsonify({"total_records": len(rows), "data": rows}), 200


# ---------------------------------------------------------------------------
# Scheduler — starts at MODULE IMPORT so it works under gunicorn too
# ---------------------------------------------------------------------------
def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)

    # Every hour
    scheduler.add_job(run_speedtest, trigger="interval", hours=1,
                      id="hourly", replace_existing=True)

    # Once shortly after startup (10s delay so the web server is up first)
    scheduler.add_job(run_speedtest, trigger="date",
                      run_date=datetime.now(), id="startup")

    scheduler.start()
    logger.info("✅ Scheduler started — runs now + every hour")


# This block runs on IMPORT (gunicorn) AND direct run (python app.py)
logger.info("=" * 55)
logger.info("🚀 Speedtest Monitor initializing...")
init_database()
start_scheduler()
logger.info("=" * 55)


if __name__ == '__main__':
    logger.info("🌐 Running Flask dev server on port %s", PORT)
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
