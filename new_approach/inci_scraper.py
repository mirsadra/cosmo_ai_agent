import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def scrape_inci_product(product_slug):
    url = f"https://incidecoder.com/products/{product_slug}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to fetch {url}")
        return None

    soup = BeautifulSoup(res.text, 'html.parser')

    # Product title
    title_tag = soup.select_one('h1')
    title = title_tag.text.strip() if title_tag else "Unknown"

    ingredients = []
    # Look for the H2 heading: "Skim through"
    skim_header_tag = soup.find('h2', string=lambda t: t and 'skim through' in t.lower()) # type: ignore
    if skim_header_tag:
        table = skim_header_tag.find_next('table')
        if table:
            rows = table.select('tbody tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    name = cols[0].get_text(strip=True)
                    function = cols[1].get_text(strip=True)
                    irr_com = cols[2].get_text(strip=True)
                    rating = cols[3].get_text(strip=True)
                    ingredients.append({
                        'name': name,
                        'function': function,
                        'irr_com': irr_com,
                        'rating': rating
                    })

    return {'product': title, 'slug': product_slug, 'ingredients': ingredients}


# Example usage
if __name__ == "__main__":
    product_slug = "the-ordinary-buffet"
    data = scrape_inci_product(product_slug)
    if data:
        print("Product:", data['product'])
        print("Ingredients:")
        for i, ing in enumerate(data['ingredients'], start=1):
            print(f"{i}. {ing['name']} | {ing['function']} | {ing['irr_com']} | {ing['rating']}")
