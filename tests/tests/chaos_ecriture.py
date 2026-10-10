import concurrent.futures
import json
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

URL = "http://localhost:8000/acheter"
PRODUCT_ID = 13
DURATION_SECONDS = 20
WORKERS = 20

stop_event = threading.Event()
results = []
lock = threading.Lock()


def buy_loop():
    while not stop_event.is_set():
        payload = json.dumps({
            "product_id": PRODUCT_ID,
            "quantity": 1,
        }).encode("utf-8")

        request = urllib.request.Request(
            URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                result = ("success", response.status)
        except urllib.error.HTTPError as error:
            result = ("http_error", error.code)
        except Exception as error:
            result = ("network_error", type(error).__name__)

        with lock:
            results.append(result)

        time.sleep(0.02)


def main():
    print("Simulation en cours pendant 20 secondes.")
    print("Ouvre un SECOND terminal PowerShell.")
    print("Lorsque tu vois ce message, attends environ 3 secondes,")
    print("puis lance : docker kill globalshop-node1")
    print("Ne ferme pas ce terminal.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(buy_loop) for _ in range(WORKERS)]

        time.sleep(DURATION_SECONDS)
        stop_event.set()

        for future in futures:
            future.result()

    counts = Counter((kind, code) for kind, code in results)

    print("\n--- Résultats de la simulation ---")
    print(f"Nombre total de requêtes : {len(results)}")
    for (kind, code), count in sorted(counts.items()):
        print(f"{kind} / {code}: {count}")


if __name__ == "__main__":
    main()
