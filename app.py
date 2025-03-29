from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_TOKEN
}


def check_product_availability(title, size):
    print(f"🛠 Richiesta ricevuta per: {title}, taglia: {size}")

    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/graphql.json"

    query = """
    query getProductByTitle($title: String!) {
      products(first: 1, query: $title) {
        edges {
          node {
            title
            variants(first: 20) {
              edges {
                node {
                  title
                  availableForSale
                  inventoryQuantity
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {"title": title}
    payload = {"query": query, "variables": variables}

    try:
        response = requests.post(url, json=payload, headers=HEADERS)
    except Exception as e:
        print("❌ Errore nella chiamata a Shopify:", str(e))
        return "Si è verificato un errore tecnico interrogando Shopify."

    print("🔍 Shopify GraphQL status:", response.status_code)

    if response.status_code != 200:
        print("⚠️ Risposta non valida:", response.text)
        return "Errore durante la richiesta a Shopify."

    try:
        data = response.json()
        print("📦 Shopify GraphQL response:", json.dumps(data, indent=2))
    except Exception as e:
        print("❌ Errore nel parsing JSON:", str(e))
        return "Errore nella lettura della risposta di Shopify."

    try:
        variants = data["data"]["products"]["edges"][0]["node"]["variants"]["edges"]
    except (KeyError, IndexError):
        return f"Il prodotto '{title}' non è stato trovato."

    for variant in variants:
        variant_title = variant["node"]["title"].lower()
        if size.lower() in variant_title:
            available = variant["node"]["availableForSale"]
            qty = variant["node"]["inventoryQuantity"]
            if available and qty > 0:
                return f"Sì, il prodotto '{title}' è disponibile in taglia {size}. Abbiamo {qty} unità."
            else:
                return f"Il prodotto '{title}' in taglia {size} non è disponibile al momento."

    return f"Il prodotto '{title}' non ha la taglia {size} disponibile."


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    function = data.get("function")
    args = data.get("arguments", {})

    print("📥 Payload ricevuto:", data)

    if function == "check_product_availability":
        title = args.get("prodotto")
        size = args.get("taglia")
        response_text = check_product_availability(title, size)
        return jsonify({"response": response_text})

    return jsonify({"response": "Funzione non riconosciuta."})


@app.route("/")
def home():
    return "✅ Webhook attivo per ElevenLabs"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)