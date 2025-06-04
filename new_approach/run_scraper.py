# run_scraper.py

from peptide_product_search import get_product_slugs_by_peptide
from inci_scraper import scrape_inci_product

peptide_name = "Palmitoyl Tetrapeptide-7"
slugs = get_product_slugs_by_peptide(peptide_name)

print(f"Found {len(slugs)} products using '{peptide_name}':")
for slug in slugs:
    print(f"\n--- Scraping: {slug} ---")
    product_data = scrape_inci_product(slug)
    if product_data:
        print(f"✅ {product_data['product']}")
        print(f"Ingredients count: {len(product_data['ingredients'])}")
