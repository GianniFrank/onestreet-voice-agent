from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # es: onestreet.myshopify.com
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")  # es: shpat_xxxxxx

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_TOKEN
}


def check_product_availability(title, size):
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

    variables = {
        "title": title
    }

    payload = {
        "query": query,
        "variables": variables
    }

    response = requests.post(url, json=payload, headers=HEADERS)

    print("🔍 Shopify GraphQL status:", response.status_code)
    print("📦 Shopify GraphQL response:", response.text)

    if response.status_code != 200:
        return "Errore durante la richiesta a Shopify."

    data = response.json()

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