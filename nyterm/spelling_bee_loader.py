import requests
from html.parser import HTMLParser
import json

class SpellingBeeLoader(HTMLParser):
    game_data = None
    def handle_data(self, data):
        if data.startswith("window.gameData"):
            data = data.replace("window.gameData =", "")
            data = json.loads(data)
            self.game_data = data

def load_spelling_bee():
    data = requests.get("https://www.nytimes.com/puzzles/spelling-bee")
    html = data.text
    parser = SpellingBeeLoader()
    parser.feed(html)
    return parser.game_data