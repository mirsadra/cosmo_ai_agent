# peptide_product_search.py

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def get_product_slugs_by_peptide(peptide_name, max_pages=20):
    """
    Search for products containing a given peptide and extract their slugs from paginated results.
    """
    base_url = "https://incidecoder.com/search/product"
    slugs = set()

    for page in range(1, max_pages + 1):
        params = {
            "query": "",
            "include": peptide_name,
            "page": page
        }
        res = requests.get(base_url, params=params, headers=headers)
        if res.status_code != 200:
            print(f"Failed to fetch page {page} for peptide '{peptide_name}'")
            break

        soup = BeautifulSoup(res.text, 'html.parser')
        product_links = soup.select('div.card-body > h3 > a')

        if not product_links:
            break  # No more results

        for link in product_links:
            href = link.get('href')
            if href and href.startswith('/products/'):
                slug = href.split('/products/')[-1]
                slugs.add(slug)

    return sorted(slugs)
