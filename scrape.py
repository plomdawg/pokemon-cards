from distutils.log import error
import sys
from unicodedata import name
import requests
from bs4 import BeautifulSoup
from time import sleep
import os
import csv
import gspread


BASE_URL = "https://www.trollandtoad.com"

SPREADSHEET_ID = "1XU6hj5jGNGAZ2o0r6gNBRwzveK9nNZiM1oOjnK4lI54"

# Login to google.
gc = gspread.service_account(filename='key.json')


class Card:
    def __init__(self, name, number, price, condition, kind, endpoint, category) -> None:
        self.name = name
        self.number = number
        self.price = price
        self.condition = condition
        self.kind = kind
        self.endpoint = endpoint
        self.category = category

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.endpoint}"

    @property
    def csv(self) -> str:
        return f"{self.category.name},{self.name},{self.number},{self.kind},{self.price},{self.condition},{self.url},{self.category.url}"


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
                name = tokens[0].strip()
                number = tokens[1].strip()
                kind = tokens[2].strip()
            except IndexError:
                continue
            # We might not find a price or condition.
            price = None
            condition = None
            # Find the listing by Troll and Toad.
            for listing in div.find_all('div', class_='row position-relative align-center py-2 m-auto'):
                img = listing.find('img')
                if img is None or img.get('title') not in "TrollAndToad Com":
                    continue
                else:
                    # Found the listing.
                    price = listing.find(
                        'div', class_='col-2 text-center p-1').text
                    condition = listing.find('a').text.strip()
                    break
            card = Card(name=name, price=price, endpoint=endpoint,
                        number=number, condition=condition, kind=kind, category=self)
            cards.append(card)

        return cards

    def get_cards(self) -> list:
        cards = []
        page_num = 1
        endpoint = f"{self.endpoint}?sort-order=A-Z&page-no={page_num}&view=list"
        page = get_page(endpoint)
        cards.extend(self.get_cards_from_page(page))

        # Go the the next page until the "next page" button is gone (end of pages).
        while page.find(class_="nextPage pageLink d-flex font-weight-bold") is not None:
            page_num += 1
            endpoint = f"{self.endpoint}?sort-order=A-Z&page-no={page_num}&view=list"
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
    # print(table)
    for link in table.find_all('a'):
        #print(f"link: {link}")
        category = Category(name=link.text, endpoint=link.get('href'))
        categories.append(category)
    return categories


categories = get_categories()

# Print each category.
i = 0
for category in categories:
    print(f"{i}. {category.name} {category.endpoint}")
    i += 1

# Write card data to a csv file.
output_file = "output.csv"
with open(output_file, "w") as f:
    try:
        i = 0
        for category in categories:
            i += 1
            cards = category.get_cards()
            for card in cards:
                f.write(card.csv + '\n')
            print(
                f"Loaded {len(cards)} cards from category {i}. '{category.name}'")

    except Exception as e:
        print(e)

# Open the google sheet.
google_sheet = gc.open_by_key(SPREADSHEET_ID)
sheet_name = "output.csv from script"

# Update the values.
google_sheet.values_update(
    sheet_name,
    params={'valueInputOption': 'USER_ENTERED'},
    body={'values': list(csv.reader(open(output_file)))}
)
