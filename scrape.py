import requests
from bs4 import BeautifulSoup
import csv
import gspread


BASE_URL = "https://www.trollandtoad.com"

SPREADSHEET_ID = "1XU6hj5jGNGAZ2o0r6gNBRwzveK9nNZiM1oOjnK4lI54"

# Login to google.
gc = gspread.service_account(filename='key.json')


def clean_text(text) -> str:
    return text.strip().replace("  ", " ").replace(",", " ")


class Card:
    def __init__(self, name, number, price, condition, kind, endpoint, category, in_stock) -> None:
        self.name = name
        self.number = number
        self.price = price
        self.condition = condition
        self.kind = kind
        self.endpoint = endpoint
        self.category = category
        self.in_stock = in_stock

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.endpoint}"

    @property
    def csv(self) -> str:
        return f"{self.category.name},{self.name},{self.number},{self.kind},{self.price},{self.condition},{self.url},{self.category.url},{self.in_stock}"


class Category:
    def __init__(self, name, endpoint) -> None:
        self.name = name.strip()
        self.endpoint = endpoint
        self.cards = []

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.endpoint}"

    def get_cards_from_page(self, page):
        cards = []

        for div in page.find_all(class_='product-col col-12 p-0 my-1 mx-sm-1 mw-100'):
            text = div.find('a', class_='card-text').text
            endpoint = div.find('a').get('href')
            tokens = text.split('-')

            # Ignore cards that don't match the format:
            #     name - number - kind
            try:
                # Remove extra spacing and double spacing.
                name = clean_text(tokens[0])
                number = clean_text(tokens[1])
                kind = clean_text(tokens[2])
            except IndexError:
                continue

            # We might not find a price or condition.
            price = None
            condition = None
            in_stock = False

            # Find the listing by Troll and Toad.
            for listing in div.find_all('div', class_='row position-relative align-center py-2 m-auto'):
                img = listing.find('img')
                if img is None or img.get('title') not in "TrollAndToad Com":
                    continue
                else:
                    # Found the listing.
                    in_stock = True
                    price = listing.find(
                        'div', class_='col-2 text-center p-1').text.replace(",", "")
                    condition = listing.find('a').text.strip()
                    break

            # Check if the listing says "OUT OF STOCK".
            out_of_stock_text = div.find(
                class_='font-weight-bold font-smaller text-muted')
            if out_of_stock_text is not None:
                if out_of_stock_text.text in "Out of Stock":
                    in_stock = False

            # Create the Card object.
            card = Card(name=name, price=price, endpoint=endpoint, number=number,
                        condition=condition, kind=kind, category=self, in_stock=in_stock)
            cards.append(card)

        return cards

    def get_cards(self) -> list:
        cards = []
        page_num = 1
        # Load 240 items per page.
        endpoint = f"{self.endpoint}?sort-order=A-Z&page-no={page_num}&view=list&items-pp=240"
        page = get_page(endpoint)
        cards.extend(self.get_cards_from_page(page))

        # Go the the next page until the "next page" button is gone (end of pages).
        while page.find(class_="nextPage pageLink d-flex font-weight-bold") is not None:
            page_num += 1
            endpoint = f"{self.endpoint}?sort-order=A-Z&page-no={page_num}&view=list&items-pp=240"
            page = get_page(endpoint)
            cards.extend(self.get_cards_from_page(page))

        return cards


def get_page(endpoint):
    url = f"{BASE_URL}{endpoint}"
    print(f"Loading data from {url}")
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def get_categories():
    categories = []
    page = get_page("/pokemon/7061")
    table = page.find(class_='row card mt-1')
    for link in table.find_all('a'):
        category = Category(name=link.text, endpoint=link.get('href'))
        categories.append(category)
    return categories


# Load the categories.
categories = get_categories()

# Print each category with a number.
for index, category in enumerate(categories):
    print(f"{index}. {category.name} {category.endpoint}")

# Blacklist categories that don't contain cards.
# From logs:
#  - Loaded 0 cards from category 9. 'Booster Boxes'
#  - Loaded 0 cards from category 13. 'Complete Sets'
#  - Loaded 0 cards from category 14. 'Elite Trainer Boxes'
#  - Loaded 0 cards from category 15. 'Funko POP! & Other Vinyl Figures'
#  - Loaded 0 cards from category 18. 'Lots & Bundles'
#  - Loaded 0 cards from category 88. 'Leonhart Exclusive Deals'
#  - Loaded 0 cards from category 97. 'Pokemon Go'
#  - Loaded 0 cards from category 139. 'Lots & Bundles'
#  - Loaded 0 cards from category 141. 'CCG Select'
#  - Loaded 0 cards from category 145. 'Sword & Shield: Star Birth [s9] Sealed Product'
blacklist = [9, 13, 14, 15, 18, 88, 97, 139, 141, 145]

# Write card data to a csv file.
output_file = "output.csv"
with open(output_file, "w") as f:
    try:
        for index, category in enumerate(categories):
            # Ignore blacklisted categories.
            if (index + 1) in blacklist:
                continue

            # Get all the cards from this category.
            cards = category.get_cards()
            for card in cards:
                f.write(card.csv + '\n')

            # Log how many cards we found in this category.
            print(
                f"Loaded {len(cards)} cards from category {index}. '{category.name}'")

    except Exception as e:
        print(e)

# Open the google sheet.
google_sheet = gc.open_by_key(SPREADSHEET_ID)
sheet_name = "output.csv from script"

# Update the values by reading the csv file.
google_sheet.values_update(
    sheet_name,
    params={'valueInputOption': 'USER_ENTERED'},
    body={'values': list(csv.reader(open(output_file)))}
)
