#!/usr/bin/env python3
import os
import time
import requests
import logging
from decimal import Decimal, InvalidOperation
import sched
from typing import Optional, Tuple
from urllib.parse import urlparse


class Config:
    QBITTORRENT_URL = os.getenv('QBITTORRENT_URL')
    SABNZBD_URL = os.getenv('SABNZBD_URL')
    SABNZBD_API_KEY = os.getenv('SABNZBD_API_KEY')

    @classmethod
    def _get_decimal(cls, env_var: str, default: str) -> Decimal:
        try:
            return Decimal(os.getenv(env_var, default))
        except InvalidOperation:
            return Decimal(default)

    @classmethod
    def MAX_LINE_SPEED_MBPS(cls) -> Decimal:
        return cls._get_decimal('MAX_LINE_SPEED_MBPS', '100')

    @classmethod
    def LIMIT_PERCENTAGE(cls) -> Decimal:
        return cls._get_decimal('LIMIT_PERCENTAGE', '0.50')

    @classmethod
    def MAX_PERCENTAGE(cls) -> Decimal:
        return cls._get_decimal('MAX_PERCENTAGE', '0.75')

    @classmethod
    def INTERVAL(cls) -> int:
        return int(os.getenv('INTERVAL', '2'))

    @classmethod
    def LOG_LEVEL(cls) -> int:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level, logging.INFO)

    @classmethod
    def validate(cls):
        for url in [cls.QBITTORRENT_URL, cls.SABNZBD_URL]:
            if not urlparse(url).scheme or not urlparse(url).netloc:
                raise ValueError(f"Invalid URL format: {url}")

        if not cls.SABNZBD_API_KEY:
            raise ValueError("Environment variable SABNZBD_API_KEY must be set")

        if cls.MAX_LINE_SPEED_MBPS() <= 0:
            raise ValueError("MAX_LINE_SPEED_MBPS must be greater than 0.")

        for name, value in [('LIMIT_PERCENTAGE', cls.LIMIT_PERCENTAGE()), ('MAX_PERCENTAGE', cls.MAX_PERCENTAGE())]:
            if not (0 <= value <= 1):
                raise ValueError(f"{name} must be between 0 and 1.")

        if cls.INTERVAL() <= 0:
            raise ValueError("INTERVAL must be greater than 0.")


class SessionManager:
    session = None

    @classmethod
    def get_session(cls) -> requests.Session:
        if cls.session is None:
            cls.session = requests.Session()
        return cls.session

    @classmethod
    def close_session(cls) -> None:
        if cls.session:
            cls.session.close()
            cls.session = None


def setup_logging() -> None:
    logging.basicConfig(
        level=Config.LOG_LEVEL(),
        format='time=%(asctime)s level=%(levelname)s message="%(message)s"',
        datefmt='%Y-%m-%dT%H:%M:%S%z'
    )

logger = logging.getLogger(__name__)
setup_logging()

scheduler = sched.scheduler(time.time, time.sleep)


def handle_request(url: str, method: str = 'GET', data: Optional[dict] = None) -> Optional[dict]:
    try:
        session = SessionManager.get_session()
        response = session.post(url, data=data) if method == 'POST' else session.get(url)
        response.raise_for_status()
        return response.json() if method == 'GET' else None
    except requests.RequestException as e:
        url = url.replace(Config.SABNZBD_API_KEY, mask(Config.SABNZBD_API_KEY))
        e = str(e).replace(Config.SABNZBD_API_KEY, mask(Config.SABNZBD_API_KEY))
        logger.error(f"Request failed for {url}: {e}")
        return None


def qbittorrent_data() -> Tuple[int, int]:
    queue_data = handle_request(f'{Config.QBITTORRENT_URL}/api/v2/torrents/info')
    limit_data = handle_request(f'{Config.QBITTORRENT_URL}/api/v2/transfer/info')
    return (
        len([t for t in queue_data if t.get('state') == 'downloading']) if queue_data else 0,
        int(limit_data.get('dl_rate_limit', 0)) if limit_data else 0
    )


def sabnzbd_data() -> Tuple[int, int]:
    data = handle_request(f'{Config.SABNZBD_URL}/api?apikey={Config.SABNZBD_API_KEY}&mode=queue&output=json')
    return (
        int(data.get('queue', {}).get('noofslots', 0)) if data else 0,
        int(data.get('queue', {}).get('speedlimit', 0)) if data else 0
    )


def mask(api_key: str, mask_length: int = 6) -> str:
    return f"{api_key[:mask_length]}{'*' * (len(api_key) - mask_length)}" if len(api_key) > mask_length else '*' * len(api_key)


def adjust_download_speeds() -> None:
    try:
        qbittorrent_queue, qbittorrent_current_limit = qbittorrent_data()
        sabnzbd_queue, sabnzbd_current_limit = sabnzbd_data()

        logger.debug(f"qbittorrent [{qbittorrent_queue} item(s) @ max {qbittorrent_current_limit} B/s]")
        logger.debug(f"sabnzbd [{sabnzbd_queue} item(s) @ max {sabnzbd_current_limit} MB/s]")

        percentage = Config.LIMIT_PERCENTAGE() if qbittorrent_queue > 0 and sabnzbd_queue > 0 else Config.MAX_PERCENTAGE()

        qbittorrent_updated_limit = int(Config.MAX_LINE_SPEED_MBPS() * percentage * 1024 * 1024)

        if qbittorrent_current_limit != qbittorrent_updated_limit:
            handle_request(f'{Config.QBITTORRENT_URL}/api/v2/transfer/setDownloadLimit', 'POST', {'limit': qbittorrent_updated_limit})
            logger.info(f"qbittorrent download limit set to {qbittorrent_updated_limit} B/s (was {qbittorrent_current_limit})...")

        sabnzbd_updated_limit = int(Config.MAX_LINE_SPEED_MBPS() * percentage)

        if sabnzbd_current_limit != sabnzbd_updated_limit:
            handle_request(f'{Config.SABNZBD_URL}/api', 'POST', {'apikey': Config.SABNZBD_API_KEY, 'mode': 'config', 'name': 'speedlimit', 'value': sabnzbd_updated_limit})
            logger.info(f"sabnzbd download limit set to {sabnzbd_updated_limit} MB/s (was {sabnzbd_current_limit})...")
    except Exception as e:
        logger.error(f"Failed to adjust download speeds: {e}")

    scheduler.enter(Config.INTERVAL(), 1, adjust_download_speeds)


def main():
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)

    logger.info(f"Starting script with config: QBITTORRENT_URL={Config.QBITTORRENT_URL}, "
                f"SABNZBD_URL={Config.SABNZBD_URL}, "
                f"SABNZBD_API_KEY={mask(Config.SABNZBD_API_KEY)}, "
                f"MAX_LINE_SPEED_MBPS={Config.MAX_LINE_SPEED_MBPS():.2f}, "
                f"LIMIT_PERCENTAGE={Config.LIMIT_PERCENTAGE():.2f}, "
                f"MAX_PERCENTAGE={Config.MAX_PERCENTAGE():.2f}, "
                f"INTERVAL={Config.INTERVAL()}, "
                f"LOG_LEVEL={Config.LOG_LEVEL()}")

    try:
        scheduler.enter(0, 1, adjust_download_speeds)
        scheduler.run()
    except (KeyboardInterrupt, SystemExit):
        SessionManager.close_session()

if __name__ == '__main__':
    main()
