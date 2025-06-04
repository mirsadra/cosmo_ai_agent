# new_approach/scrape_product_inci_by_slug.py

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://incidecoder.com/products/"

def load_slugs(slug_file_path):
    with open(slug_file_path, 'r') as f:
        return json.load(f)

def scrape_product_data(slug):
    url = BASE_URL + slug
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to fetch: {slug}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    try:
        product_name = soup.select_one("h1.klavikab").text.strip()
    except AttributeError:
        product_name = slug.replace("-", " ").title()

    # Ingredient table
    inci_rows = soup.select("table.ingredient-table tbody tr")

    ingredients = []
    for row in inci_rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            name = cells[0].text.strip()
            function_cell = cells[1]
            function = [span.text.strip() for span in function_cell.select("span")]
            is_goodie = "goodie" in function_cell.get("class", [])
            is_irritant = "irritant" in function_cell.get("class", [])
            ingredients.append({
                "name": name,
                "function": function,
                "is_goodie": is_goodie,
                "is_irritant": is_irritant
            })

    return {
        "slug": slug,
        "product_name": product_name,
        "url": url,
        "ingredients": ingredients
    }

def save_results(results, peptide_name):
    file_path = f"data/inci/{peptide_name.replace(' ', '_').lower()}_products.json"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Saved: {file_path}")

def main():
    peptide_name = input("🔍 Enter the peptide name (same as slug file): ").strip()
    slug_file_path = f"data/slugs/{peptide_name.replace(' ', '_').lower()}.json"

    print(f"📂 Loading slugs from: {slug_file_path}")
    slugs = load_slugs(slug_file_path)

    all_products = []
    for slug in tqdm(slugs, desc="🔎 Scraping products"):
        product_data = scrape_product_data(slug)
        if product_data:
            all_products.append(product_data)
        time.sleep(1.5)  # polite delay

    save_results(all_products, peptide_name)

if __name__ == "__main__":
    main()
