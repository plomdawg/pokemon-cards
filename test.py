import scrape

categories = scrape.get_categories()
print(f"Loaded {len(categories)} categories")

# Take the first category "All Singles"
#category = categories[0]
#print(category.name, category.url, category.cards)

#print("Testing buybox scraping...")
#page = scrape.get_page("/pokemon/black-white-10-plasma-blast/8551?sort-order=A-Z&page-no=1&view=list&items-pp=240")
#category.get_cards_from_page(page, start=20)

#print("Testing card price scraping...")
#page = scrape.get_page("/pokemon/all-singles/7088?sort-order=A-Z&page-no=1&view=list&items-pp=240")
#category.get_cards_from_page(page, start=64, end=69)


def fill_missing_categories(indicies):
    cards = scrape.get_cards([categories[index] for index in indicies])
    scrape.update_csv("missing.csv", cards)
        
missing_categories = [3, 8, 12, 13, 14, 17, 87, 96, 138, 140, 144]
fill_missing_categories(missing_categories)