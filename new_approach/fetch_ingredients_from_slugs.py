# fetch_ingredients_from_slugs_grouped.py

import os
import json
import time
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def load_slugs(json_path):
    with open(json_path, "r") as f:
        return json.load(f)

def scrape_inci_product(product_slug):
    url = f"https://incidecoder.com/products/{product_slug}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, 'html.parser')

    title_tag = soup.select_one('h1')
    title = title_tag.text.strip() if title_tag else "Unknown"

    ingredients = []
    skim_header_tag = soup.find('h2', string=lambda t: t and 'skim through' in t.lower())
    if skim_header_tag:
        table = skim_header_tag.find_next('table')
        if table:
            rows = table.select('tbody tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    ingredients.append({
                        'name': cols[0].get_text(strip=True),
                        'function': cols[1].get_text(strip=True),
                        'irr_com': cols[2].get_text(strip=True),
                        'rating': cols[3].get_text(strip=True)
                    })

    return {
        'name': title,
        'slug': product_slug,
        'ingredients': ingredients
    }

def save_grouped_products(peptide_slug, peptide_name, all_products):
    os.makedirs("data/peptides", exist_ok=True)
    path = f"data/peptides/{peptide_slug}.json"
    with open(path, "w") as f:
        json.dump({
            "peptide": peptide_name,
            "products": all_products
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {path}")

def main():
    peptide_slug = input("🔍 Enter peptide slug (e.g. palmitoyl_tetrapeptide_7): ").strip()
    filepath = f"data/slugs/{peptide_slug}.json"

    if not os.path.exists(filepath):
        print("⚠️ Slug list not found.")
        return

    slugs = load_slugs(filepath)
    all_products = []

    for entry in slugs:
        print(f"🔎 Fetching: {entry['name']} → {entry['slug']}")
        product = scrape_inci_product(entry['slug'])

        if product and product['ingredients']:
            all_products.append(product)
        else:
            print(f"⚠️ Skipped or no ingredients found: {entry['slug']}")

        time.sleep(1.0)

    if all_products:
        save_grouped_products(peptide_slug, peptide_slug.replace("_", " ").title(), all_products)
    else:
        print("❌ No products saved.")

if __name__ == "__main__":
    main()
