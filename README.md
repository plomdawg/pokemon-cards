# pokemon-cards

Scripts to scrape pokemon card price data to be used in a spreadsheet.

## Usage

1. [Authenticate with Google Sheets](https://docs.gspread.org/en/latest/oauth2.html) to get your `key.json`. Place this in the main folder.

1. Create a copy of [this spreadsheet](https://docs.google.com/spreadsheets/d/1qyP4u944LPuUsc1ZgTTibGZCifSkw76Vf6p7X0m9Hdg/edit?usp=sharing) and invite the email from `key.json` with edit access. 

1. Replace the spreadsheet ID in [scrape.py](scrape.py) with the spreadsheet ID from the URL (the string after `/d/`).

1. Install [Python 3](https://www.python.org/downloads/).

1. Install the dependencies
```bash
pip install beautifulsoup4 gspread
```

1. Run the scraper

```bash
python scrape.py
```


## Example Output

console:

```console
avalon@homer:~/cards$ python scrape.py 
Loaded 2049 cards from category 1. 'All  Singles'
Loaded 4651 cards from category 2. 'Collector's Vault'
Loaded 2088 cards from category 3. 'Non-English  Cards'
Loaded 67 cards from category 4. 'Official  Plushes, Toys, & Apparel'
Loaded 4638 cards from category 5. 'PSA & Beckett Graded  Cards'
Loaded 145 cards from category 6. '25th Anniversary'
Loaded 54 cards from category 7. 'Battle Arena Decks'
Loaded 4 cards from category 8. 'Blister Packs'
```

`output.csv`:

```csv
All Singles,Pikachu,5/25,Full Art Holo Rare,$0.79,Near-Mint English Pokemon Card,https://www.trollandtoad.com/pokemon/celebrations-singles/pikachu-5-25-full-art-holo-rare/1733003,https://www.trollandtoad.com/pokemon/all-singles/7088
All Singles,Pikachu V,157/172,Full Art Ultra Rare,$15.99,Near-Mint English Pokemon Card,https://www.trollandtoad.com/pokemon/sword-shield-brilliant-stars-singles/pikachu-v-157-172-full-art-ultra-rare/1744371,https://www.trollandtoad.com/pokemon/all-singles/7088
All Singles,Piloswine,032/189,Uncommon,$0.35,Near-Mint English Pokemon Card,https://www.trollandtoad.com/pokemon/sword-shield-astral-radiance-singles/piloswine-032-189-uncommon/1750869,https://www.trollandtoad.com/pokemon/all-singles/7088
All Singles,Piloswine,032/189,Uncommon Reverse Holo,$0.39,Near-Mint Reverse Foil Pokemon Card,https://www.trollandtoad.com/pokemon/sword-shield-astral-radiance-reverse-holo-singles/piloswine-032-189-uncommon-reverse-holo/1750997,https://www.trollandtoad.com/pokemon/all-singles/7088
```

## Spreadsheet Setup

1. Fill in your cards in the first sheet. They will light up green if found in the list of cards.
![image](https://user-images.githubusercontent.com/6510862/174883533-a09136ba-6702-4860-9ea0-9720391dd3ba.png)
1. The `sorted cards` sheet will now populate.
![image](https://user-images.githubusercontent.com/6510862/174884615-be7ff366-e9f3-46c3-8dd0-2adb5dcdf467.png)

