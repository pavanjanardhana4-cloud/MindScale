"""
Google Fit service helpers.

Provides small, focused functions to fetch:
- Steps for last 7 days
- Sleep duration for last 7 days
- Heart rate averages for last 7 days

All functions expect a google.oauth2.credentials.Credentials instance.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict

import requests


FIT_AGGREGATE_URL = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"


def _unix_millis(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _last_n_days_window(days: int = 7) -> (int, int):
    """Return (start_ms, end_ms) for the last N full days in UTC."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return _unix_millis(start), _unix_millis(end)


def _aggregate(creds, body: dict) -> dict:
    """Call the Google Fit aggregate endpoint with the given request body."""
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(FIT_AGGREGATE_URL, json=body, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_steps_last_7_days(creds) -> List[Dict[str, int]]:
    """Return steps per day for the last 7 days: [{'date': 'YYYY-MM-DD', 'steps': int}, ...]."""
    start_ms, end_ms = _last_n_days_window(7)
    body = {
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms,
        "aggregateBy": [
            {"dataTypeName": "com.google.step_count.delta"},
        ],
        "bucketByTime": {"durationMillis": 24 * 60 * 60 * 1000},
    }
    data = _aggregate(creds, body)
    results: List[Dict[str, int]] = []
    for bucket in data.get("bucket", []):
        start = int(bucket.get("startTimeMillis", start_ms))
        day = datetime.fromtimestamp(start / 1000, tz=timezone.utc).date().isoformat()
        steps_total = 0
        for ds in bucket.get("dataset", []):
            for point in ds.get("point", []):
                vals = point.get("value", [])
                if vals:
                    steps_total += int(vals[0].get("intVal", 0))
        results.append({"date": day, "steps": steps_total})
    return results


def get_sleep_last_7_days(creds) -> List[Dict[str, float]]:
    """
    Return sleep duration (in hours) per day for last 7 days:
    [{'date': 'YYYY-MM-DD', 'hours': float}, ...]

    This uses com.google.sleep.segment and sums segment durations per day.
    """
    start_ms, end_ms = _last_n_days_window(7)
    body = {
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms,
        "aggregateBy": [
            {"dataTypeName": "com.google.sleep.segment"},
        ],
        "bucketByTime": {"durationMillis": 24 * 60 * 60 * 1000},
    }
    data = _aggregate(creds, body)
    results: List[Dict[str, float]] = []
    for bucket in data.get("bucket", []):
        start = int(bucket.get("startTimeMillis", start_ms))
        day = datetime.fromtimestamp(start / 1000, tz=timezone.utc).date().isoformat()
        sleep_ms = 0
        for ds in bucket.get("dataset", []):
            for point in ds.get("point", []):
                s = int(point.get("startTimeNanos", 0) or 0)
                e = int(point.get("endTimeNanos", 0) or 0)
                if e > s:
                    sleep_ms += (e - s) / 1_000_000.0
        hours = round(sleep_ms / (1000 * 60 * 60), 2)
        results.append({"date": day, "hours": hours})
    return results


def get_heart_rate_last_7_days(creds) -> List[Dict[str, float]]:
    """
    Return average heart rate per day for last 7 days:
    [{'date': 'YYYY-MM-DD', 'avg_bpm': float}, ...].
    """
    start_ms, end_ms = _last_n_days_window(7)
    body = {
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms,
        "aggregateBy": [
            {"dataTypeName": "com.google.heart_rate.bpm"},
        ],
        "bucketByTime": {"durationMillis": 24 * 60 * 60 * 1000},
    }
    data = _aggregate(creds, body)
    results: List[Dict[str, float]] = []
    for bucket in data.get("bucket", []):
        start = int(bucket.get("startTimeMillis", start_ms))
        day = datetime.fromtimestamp(start / 1000, tz=timezone.utc).date().isoformat()
        total = 0.0
        count = 0
        for ds in bucket.get("dataset", []):
            for point in ds.get("point", []):
                vals = point.get("value", [])
                if vals:
                    bpm = vals[0].get("fpVal")
                    if bpm is not None:
                        total += float(bpm)
                        count += 1
        avg = round(total / count, 1) if count else 0.0
        results.append({"date": day, "avg_bpm": avg})
    return results

