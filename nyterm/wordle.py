import util
from datetime import datetime
from curses import window

class Wordle:
    BASE_URL = "https://www.nytimes.com/svc/wordle/v2/"

    year = None
    month = None
    day = None
    game_data = None

    solution = None
    def __init__(self, year, month, day):
        self.year = str(year)
        self.month = str(month)
        self.day = str(day)
        self.load()

    def get_from_date(self, date: datetime):
        return Wordle(date.year, date.month, date.day)

    def get_url_for_date(self):
        return self.BASE_URL + "/" + util.get_file_name_for_date(self.year, self.month, self.day)
    
    def load(self):
        self.game_data = util.load_json_from_url(self.get_url_for_date())
        if self.game_data != None:
            self.solution = self.game_data["solution"]

    def start(self, stdscr: window):
        while True:
            stdscr.clear()
            stdscr.addstr(self.solution)
            stdscr.refresh()