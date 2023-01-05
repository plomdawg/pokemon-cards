import scrape

categories = scrape.get_categories()
print(f"Loaded {len(categories)} categories")

# Take the first category "All Singles"
category = categories[0]
print(category.name, category.url, category.cards)

page = scrape.get_page("/pokemon/all-singles/7088?sort-order=A-Z&page-no=1&view=list&items-pp=240")
category.get_cards_from_page(page, start=64, end=69)
