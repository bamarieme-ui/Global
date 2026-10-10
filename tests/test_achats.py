import concurrent.futures
import json
import urllib.error
import urllib.request
from collections import Counter

URL = "http://localhost:8000/acheter"
PRODUCT_ID = 1
TOTAL_REQUESTS = 100


def buy_one(_):
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
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
            return ("success", response.status, body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return ("rejected", error.code, body)
    except Exception as error:
        return ("error", type(error).__name__, str(error))


def main():
    print(f"Envoi de {TOTAL_REQUESTS} achats simultanes...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as pool:
        results = list(pool.map(buy_one, range(TOTAL_REQUESTS)))

    counts = Counter(result[0] for result in results)

    print("\n--- RESULTATS ---")
    print(f"Achats acceptes : {counts['success']}")
    print(f"Achats refuses  : {counts['rejected']}")
    print(f"Erreurs inattendues : {counts['error']}")

    print("\nCodes HTTP :")
    print(Counter(str(result[1]) for result in results))

    try:
        with urllib.request.urlopen(
            f"http://localhost:8000/produits/{PRODUCT_ID}",
            timeout=10,
        ) as response:
            product = json.loads(response.read().decode("utf-8"))
            final_stock = product["stock"]

        print(f"\nStock final observe par l'API : {final_stock}")
    except Exception as error:
        final_stock = None
        print(f"\nImpossible de lire le stock final : {error}")

    print("\n--- VERDICT ---")
    if (
        counts["success"] == 10
        and counts["rejected"] == 90
        and counts["error"] == 0
        and final_stock == 0
    ):
        print("SUCCES : protection contre la survente validee.")
    else:
        print("RESULTAT A ANALYSER : les criteres attendus ne sont pas tous satisfaits.")


if __name__ == "__main__":
    main()
