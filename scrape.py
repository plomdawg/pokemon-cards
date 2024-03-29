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
        name = clean_text(link.text)
        category = Category(name=name, endpoint=link.get('href'))
        categories.append(category)
    return categories


class Card:
    def __init__(self, name, number, price, price_source, condition, kind, endpoint, category, in_stock) -> None:
        self.name = name
        self.number = number
        self.price = price
        self.price_source = price_source
        self.condition = condition
        self.kind = kind
        self.endpoint = endpoint
        self.category = category
        self.in_stock = in_stock

    def __str__(self) -> str:
        return f"{self.name} - {self.number} - {self.kind} - {self.price} - {self.price_source} - {self.condition} - {self.url} - {self.in_stock}"

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.endpoint}"

    @property
    def csv(self) -> str:
        return f"{self.category.name},{self.name},{self.number},{self.kind},{self.price},{self.condition},{self.url},{self.category.url},{self.in_stock},{self.price_source}"


class Category:
    def __init__(self, name, endpoint) -> None:
        self.name = name
        self.endpoint = endpoint
        self.cards = []

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.endpoint}"

    def get_cards_from_page(self, page, start=0, end=None):
        self.cards = []

        for div in page.find_all(class_='product-col col-12 p-0 my-1 mx-sm-1 mw-100')[start:end]:
            text = div.find('a', class_='card-text').text
            endpoint = div.find('a').get('href')
            tokens = text.split(' - ')

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
            price_source = None
            condition = None
            in_stock = False

            # Find all listings for this card.
            listings = div.find_all(
                'div', class_='row position-relative align-center py-2 m-auto')

            # Find the listing by Troll and Toad.
            for listing in listings:
                img = listing.find('img')
                if img is None or img.get('title') not in "TrollAndToad Com":
                    continue
                else:
                    # Found the listing.
                    in_stock = True
                    # Remove commas from dollar amount.
                    price = listing.find(
                        'div', class_='col-2 text-center p-1').text.replace(",", "")
                    condition = listing.find('a').text.strip()
                    price_source = "TNT Listing"
                    break

            # Check if the listing says "OUT OF STOCK".
            out_of_stock_text = div.find(
                class_='font-weight-bold font-smaller text-muted')
            if out_of_stock_text is not None:
                if out_of_stock_text.text in "Out of Stock":
                    in_stock = False

            # If we don't have a price, open the card page and get the price.
            if price is None:
                print(
                    f"No price for card {name} - {number}. Opening card page to get price: {endpoint}")
                card_page = get_page(endpoint)

                # Try to load the TNT price from the buybox on the right of the page.
                buy_box_div = card_page.find(class_='buyBox')
                card_body_div = buy_box_div.find(class_='card-body py-2')
                if card_body_div is None:
                    print("No buy box found.")
                else:
                    price_box_div = card_body_div.find(
                        class_='d-flex flex-column text-center')
                    if price_box_div is None:
                        print("No price box found.")
                    else:
                        price = price_box_div.find(
                            class_='font-weight-bold').text.strip()
                        price_source = price_box_div.find(
                            class_='flex-grow-1').text.strip()
                        condition_div = card_body_div.find(
                            class_='mx-1 flex-grow-1')
                        if condition_div:
                            condition = condition_div.find('div').text.strip()

                # If that fails, try to find the first vendor price.
                if price is None and listings:
                    print("Falling back to vendor price.")
                    listing = listings[0]
                    # Remove commas from dollar amount.
                    price = listing.find(
                        'div', class_='col-2 text-center p-1').text.replace(",", "")
                    condition = listing.find('a').text.strip()

                    # Extract the vendor name from the image.
                    img = listing.find('img')
                    price_source = img.get('title')

                # If we are still without a price, check the buybox again for a price.
                if price is None and buy_box_div:
                    print("Falling back to buy box price.")
                    card_header_div = buy_box_div.find(class_='card-header')
                    price_div = card_header_div.find('span')
                    if price_div:
                        price = price_div.text.strip()
                        price_source = "TNT Buy Box"

            if price is None:
                price_source = None

            # Create the Card object.
            card = Card(name=name, price=price, price_source=price_source, endpoint=endpoint, number=number,
                        condition=condition, kind=kind, category=self, in_stock=in_stock)
            print(f" - Added {len(self.cards)+1}. {card}")
            self.cards.append(card)

        return self.cards

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


def update_csv(csv_file, cards):
    print(f"Writing {len(cards)} cards to {csv_file}.")
    # Write card data to a csv file.
    with open(csv_file, "w") as f:
        # Write the cards to the csv file.
        for card in cards:
            f.write(card.csv + '\n')

def get_cards(categories):
    cards = []
    for index, category in enumerate(categories):
        # Print each category with a number.
        print(f"{index}. {category.name} {category.endpoint}")
        # Get all the cards from this category.
        cards.extend(category.get_cards())
        # Log how many cards we found in this category.
        print(
            f"Loaded {len(cards)} cards from category {index}. '{category.name}'")
    return cards

def update_google_sheet(csv_file):
    # Open the google sheet.
    google_sheet = gc.open_by_key(SPREADSHEET_ID)
    sheet_name = "output.csv from script"

    # Update the values by reading the csv file.
    google_sheet.values_update(
        sheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csv_file)))}
    )

def main():
    csv_file = "output.csv"
    categories = get_categories()
    cards = get_cards(categories)
    update_csv(csv_file, cards)
    update_google_sheet(csv_file)


if __name__ == "__main__":
    main()
