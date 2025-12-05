import os
import time
import logging
from typing import Dict, Tuple

import psycopg2
import redis
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("HealthMonitor")


BACKEND_AUTH_URL = os.getenv("BACKEND_AUTH_URL", "http://backend-auth:8000")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend-api:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@postgres:5432/restaurant",
)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")


def _detect_redis_port() -> int:

    raw = os.getenv("REDIS_PORT") or os.getenv("REDIS_SERVICE_PORT") or "6379"
    try:
        return int(raw)
    except ValueError:

        if ":" in raw:
            try:
                return int(raw.rsplit(":", 1)[1])
            except ValueError:
                pass

    return 6379


REDIS_PORT = _detect_redis_port()


def check_http_service(name: str, url: str, timeout: float = 5.0) -> Tuple[bool, str]:
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.ok:
            return True, f"{name}: OK ({resp.status_code})"
        return False, f"{name}: FAIL ({resp.status_code})"
    except Exception as e:
        return False, f"{name}: ERROR ({e})"


def check_backend_auth() -> Tuple[bool, str]:
    return check_http_service("backend-auth /health", f"{BACKEND_AUTH_URL}/health")


def check_backend_api() -> Tuple[bool, str]:
    return check_http_service("backend-api /health", f"{BACKEND_API_URL}/health")


def check_cache_via_api() -> Tuple[bool, str]:
    return check_http_service("backend-api /cache-test", f"{BACKEND_API_URL}/cache-test")


def check_frontend() -> Tuple[bool, str]:
    return check_http_service("frontend /", f"{FRONTEND_URL}/")


def check_database() -> Tuple[bool, str]:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            _ = cur.fetchone()
        conn.close()
        return True, "postgres: OK"
    except Exception as e:
        return False, f"postgres: ERROR ({e})"


def check_redis() -> Tuple[bool, str]:
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return True, "redis: OK"
    except Exception as e:
        return False, f"redis: ERROR ({e})"


def monitor_all_services() -> Dict[str, bool]:
    checks = {
        "backend_auth": check_backend_auth,
        "backend_api": check_backend_api,
        "cache_via_api": check_cache_via_api,
        "frontend": check_frontend,
        "database": check_database,
        "redis": check_redis,
    }

    results: Dict[str, bool] = {}
    logger.info("=" * 60)
    logger.info("Health check results:")

    for name, func in checks.items():
        ok, message = func()
        results[name] = ok
        if ok:
            logger.info(f"[OK ] {message}")
        else:
            logger.warning(f"[FAIL] {message}")

    logger.info("=" * 60)
    return results


if __name__ == "__main__":
    logger.info("Health Monitor Service Started")
    logger.info("Waiting 15 seconds before first check to let services start...")
    time.sleep(15)
    
    logger.info("Starting monitoring services every 60 seconds...")

    check_interval = 10

    while True:
        try:
            monitor_all_services()
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        logger.info(f"Next check in {check_interval} seconds...")
        time.sleep(check_interval)


