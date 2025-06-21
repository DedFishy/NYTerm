import curses
import time
from const import COLORS
from wordle import Wordle
import util
import datetime

TODAY = datetime.datetime.now()

class Game:

    selected_year = TODAY.year
    selected_month = TODAY.month
    selected_day = TODAY.day

    stdscr: curses.window = None

    running = True

    selected = 0
    OPTIONS = {}

    KEYS = {}

    def __init__(self):
        self.OPTIONS = {
            "Wordle": self.start_wordle,
            "Quit": self.quit,
        }

        self.KEYS = {
            "KEY_DOWN": self.key_down,
            "KEY_UP": self.key_up,
            "\n": lambda: self.OPTIONS[list(self.OPTIONS.keys())[self.selected]]()
        }

        for option in list(self.OPTIONS.keys()):
            self.OPTIONS["- " + option] = self.OPTIONS[option]
            del self.OPTIONS[option]

    def start_wordle(self):
        do_start = self.select_ymd("Wordle")
        if do_start:
            wordle = Wordle(self.selected_year, self.selected_month, self.selected_day)
            wordle.start(self.stdscr)

    def quit(self):
        self.running = False

    def key_down(self): 
        if self.selected < len(self.OPTIONS)-1: self.selected += 1
    def key_up(self): 
        if self.selected > 0: self.selected -= 1

    def select_ymd(self, game_title):
        
        inputs = {
            "Year": self.selected_year,
            "Month": self.selected_month,
            "Day": self.selected_day,
            "Start": True,
            "Cancel": False
        }
        input_values, result = util.run_row_selector(inputs, self.stdscr, 3, f"Starting {game_title}")
        self.selected_year = input_values["Year"]
        self.selected_month = input_values["Month"]
        self.selected_day = input_values["Day"]
        return result

    def render(self):
        self.stdscr.clear()
        rows_to_render = {
            "NYTerminal": COLORS["TITLE"], 
            "The NYT games implemented in the terminal.": COLORS["SUBTITLE"], 
            "By Boyne Gregg": COLORS["SUBTITLE"]
            }
        i = 0
        for option in self.OPTIONS.keys():
            if i == self.selected: rows_to_render[option] = COLORS["SELECTED_OPTION"]
            else: rows_to_render[option] = COLORS["UNSELECTED_OPTION"]
            i += 1

        util.render_rows_to_center(rows_to_render, self.stdscr)
        

    def start(self, stdscr: curses.window):

        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)

        curses.curs_set(False)
        
        self.stdscr = stdscr
        while self.running:
            self.render()
            key = self.stdscr.getkey()
            if key in self.KEYS.keys():
                self.KEYS[key]()
            else:
                self.OPTIONS[key] = lambda: None
        

def run():
    game = Game()
    
    curses.wrapper(game.start)
