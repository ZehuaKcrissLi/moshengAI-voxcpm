"""
TTS end-to-end benchmark (v0.1).

This script measures:
- Success rate
- End-to-end latency (submit -> completed/failed)

It exercises the real flow:
1) POST /auth/login (optional, if token not provided)
2) POST /tts/generate (enqueues)
3) Poll GET /tts/status/{task_id} until completed/failed

No try/except is used by design (fail fast).

Usage examples:
  source .venv/bin/activate
  python tools/tts_benchmark.py --voice-id "female/xxx.wav" --email "a@b.com" --password "xxx" --requests 20 --concurrency 5
  python tools/tts_benchmark.py --voice-id "female/xxx.wav" --token "$TOKEN"
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.request
import urllib.parse


def http_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None) -> dict:
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def http_form(method: str, url: str, form: dict, headers: dict | None = None) -> dict:
    encoded = urllib.parse.urlencode(form).encode("utf-8")
    req_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url=url, data=encoded, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def login(base_url: str, email: str, password: str) -> str:
    data = http_form(
        "POST",
        f"{base_url}/auth/login",
        {"username": email, "password": password},
    )
    return data["access_token"]


def run_one(base_url: str, token: str, voice_id: str, text: str, poll_interval_s: float) -> tuple[bool, float, str]:
    start = time.time()
    resp = http_json(
        "POST",
        f"{base_url}/tts/generate",
        {"text": text, "voice_id": voice_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = resp["task_id"]

    while True:
        status = http_json(
            "GET",
            f"{base_url}/tts/status/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        state = status["status"]
        if state in {"completed", "failed"}:
            elapsed = time.time() - start
            return (state == "completed", elapsed, task_id)
        time.sleep(poll_interval_s)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = int(round((p / 100.0) * (len(values_sorted) - 1)))
    return values_sorted[k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:38000")
    parser.add_argument("--token", default="")
    parser.add_argument("--email", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--text", default="你好，这是一条用于基准测试的语音合成请求。")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    args = parser.parse_args()

    if not args.token:
        if not args.email or not args.password:
            raise ValueError("Provide --token OR (--email and --password)")
        token = login(args.base_url, args.email, args.password)
    else:
        token = args.token

    n = int(args.requests)
    c = int(args.concurrency)
    if n <= 0:
        raise ValueError("--requests must be positive")
    if c <= 0:
        raise ValueError("--concurrency must be positive")

    latencies: list[float] = []
    failures: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=c) as pool:
        futures = [
            pool.submit(run_one, args.base_url, token, args.voice_id, args.text, float(args.poll_interval))
            for _ in range(n)
        ]
        for f in concurrent.futures.as_completed(futures):
            ok, elapsed, task_id = f.result()
            if ok:
                latencies.append(elapsed)
            else:
                failures.append(task_id)

    success = len(latencies)
    failed = len(failures)
    success_rate = (success / n) * 100.0

    print("=" * 72)
    print("MoshengAI TTS Benchmark (v0.1)")
    print("=" * 72)
    print(f"Base URL:     {args.base_url}")
    print(f"Voice ID:     {args.voice_id}")
    print(f"Requests:     {n}")
    print(f"Concurrency:  {c}")
    print(f"Success:      {success}")
    print(f"Failed:       {failed}")
    print(f"Success rate: {success_rate:.1f}%")
    if latencies:
        print("-" * 72)
        print(f"Avg:   {statistics.mean(latencies):.2f}s")
        print(f"P50:   {percentile(latencies, 50):.2f}s")
        print(f"P95:   {percentile(latencies, 95):.2f}s")
        print(f"Max:   {max(latencies):.2f}s")
    if failures:
        print("-" * 72)
        print("Failed task_ids (first 10):")
        for tid in failures[:10]:
            print(f"- {tid}")
    print("=" * 72)


if __name__ == "__main__":
    main()

