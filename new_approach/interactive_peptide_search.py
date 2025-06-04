import os
import json
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def slugify_peptide(peptide_name):
    return peptide_name.lower().replace(" ", "_")

def fetch_product_names_by_peptide(peptide_name, max_pages=20):
    base_url = "https://incidecoder.com/search/product"
    all_products = []

    for page in range(1, max_pages + 1):
        params = {
            "query": "",
            "include": peptide_name,
            "page": page
        }
        res = requests.get(base_url, params=params, headers=headers)
        if res.status_code != 200:
            print(f"❌ Failed to fetch page {page} for peptide '{peptide_name}'")
            break

        soup = BeautifulSoup(res.text, 'html.parser')
        product_links = soup.select('div.std-side-padding > a.klavika.simpletextlistitem')

        if not product_links:
            print(f"📭 No more results found after page {page - 1}")
            break

        page_products = []
        for link in product_links:
            product_name = link.text.strip()
            href = link.get('href')
            slug = href.split('/products/')[-1] if href and '/products/' in href else None
            if slug:
                page_products.append({"name": product_name, "slug": slug})

        all_products.extend(page_products)

    return all_products

def save_slugs(peptide_name, products):
    slugified = slugify_peptide(peptide_name)
    out_path = f"data/slugs/{slugified}.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved {len(products)} products to {out_path}")

def main():
    peptide_name = input("🔍 Enter a peptide name to search: ").strip()
    print(f"\n🔎 Searching for products containing: {peptide_name}\n")

    products = fetch_product_names_by_peptide(peptide_name)

    if not products:
        print("⚠️ No products found.")
        return

    # # Print in same nice format
    # for i, p in enumerate(products, 1):
    #     print(f"  {i:2d}. {p['name']}  →  slug: {p['slug']}")

    # Save
    save_slugs(peptide_name, products)

if __name__ == "__main__":
    main()
