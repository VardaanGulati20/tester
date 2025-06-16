import requests

def main():
    print("\n=====  Chat Assistant =====")
    ref_site = input(">>> Reference Website: ").strip()
    question = input(">>> Your Question: ").strip()

    payload = {
        "reference_site": ref_site,
        "query": question
    }

    try:
        res = requests.post("http://localhost:8000/ask", json=payload)
        res.raise_for_status()
        print("\n[🧠] Response:\n")
        print(res.json()["response"])
    except Exception as e:
        print(f"[❌] Error: {e}")

if __name__ == "__main__":
    main()
