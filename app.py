from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # es: onestreet.myshopify.com

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_PASSWORD
}

def check_product_availability(title, size):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/products.json?title={title}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return "Non riesco a recuperare le informazioni dal sistema."

    data = r.json()
    if not data["products"]:
        return f"Il prodotto '{title}' non è disponibile al momento."

    for variant in data["products"][0]["variants"]:
        if size.lower() in variant["title"].lower():
            return f"Sì, il prodotto '{title}' è disponibile in taglia {size}."
    return f"Al momento la taglia {size} del prodotto '{title}' non è disponibile."

@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.get_json()
    function = data.get("function")
    args = data.get("arguments", {})

    if function == "check_product_availability":
        product = args.get("prodotto")
        size = args.get("taglia")
        response_text = check_product_availability(product, size)
        return jsonify({"response": response_text})

    return jsonify({"response": "Funzione non riconosciuta."})

@app.route("/")
def home():
    return "✅ Webhook attivo per ElevenLabs"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)