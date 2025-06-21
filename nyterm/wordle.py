import curses
import util
from datetime import datetime
from curses import window
from const import COLORS
from importlib import resources as impresources
import word_lists

class Wordle:
    BASE_URL = "https://www.nytimes.com/svc/wordle/v2/"
    LETTER_WIDTH = 5
    LETTER_HEIGHT = 3

    year = None
    month = None
    day = None
    game_data = None

    guesses = 0

    did_win = False
    letters = "abcdefghijklmnopqrstuvwxyz"
    letter_grid = []

    with (impresources.files(word_lists) / "wordle.txt").open("rt") as word_list_file:
        allowed_words = word_list_file.readlines()

    solution = None
    def __init__(self, year, month, day):
        self.year = str(year)
        self.month = str(month)
        self.day = str(day)
        self.letter_grid = [[(" ", 0) for _ in range(5)] for _ in range(6)]
        self.guesses = 0
        self.did_win = False
        self.load()

    def get_from_date(self, date: datetime):
        return Wordle(date.year, date.month, date.day)

    def get_url_for_date(self):
        return self.BASE_URL + "/" + util.get_file_name_for_date(self.year, self.month, self.day)
    
    def load(self):
        self.game_data = util.load_json_from_url(self.get_url_for_date())
        if self.game_data != None:
            self.solution = self.game_data["solution"]

    def construct_letter_tile(self, letter):
        top = "┌───┐"
        middle = "│ " + str(letter).upper() + " │"
        bottom = "└───┘"
        return top, middle, bottom
    
    def draw_letter_grid(self, stdscr: window):
        start_coord_yx = util.get_starting_dimensions_yx(self.LETTER_WIDTH * 5, self.LETTER_HEIGHT * 6, stdscr.getmaxyx())
        y = start_coord_yx[0]
        for row in self.letter_grid:
            x = start_coord_yx[1]
            for letter_tup in row:
                letter = letter_tup[0]
                color = letter_tup[1]
                letter_tile = self.construct_letter_tile(letter)

                stdscr.addstr(y+0, x, letter_tile[0], curses.color_pair(color))
                stdscr.addstr(y+1, x, letter_tile[1], curses.color_pair(color))
                stdscr.addstr(y+2, x, letter_tile[2], curses.color_pair(color))
                x+=self.LETTER_WIDTH
            y+=self.LETTER_HEIGHT
        
        message = "Good luck!"
        if self.did_win:
            message = "Congratulations!"
        elif self.guesses > 5:
            message = "Too bad! Solution: " + self.solution
        stdscr.addstr(y, start_coord_yx[1], message.center(self.LETTER_WIDTH*5))

    def process_current_guess(self):
        current_guess = [x[0] for x in self.letter_grid[self.guesses]]
        solution = list(self.solution)
        colors = [0,0,0,0,0]

        # Process Green
        for i in range(0, 5):
            if current_guess[i] == solution[i]:
                colors[i] = COLORS["GREEN"]
                current_guess[i] = " "
                solution[i] = " "
        # Process Yellow
        for i in range(0, 5):
            if current_guess[i] != " ":
                if current_guess[i] in solution:
                    colors[i] = COLORS["YELLOW"]
                    solution[solution.index(current_guess[i])] = " "
                    current_guess[i] = " "
        
        for i in range(0, 5):
            old_tup = self.letter_grid[self.guesses][i]
            self.letter_grid[self.guesses][i] = (old_tup[0], colors[i])

        util._log(current_guess, solution, colors)

        self.guesses += 1
        return colors.count(COLORS["GREEN"]) == len(colors)

    def start(self, stdscr: window):
        current_character_index = 0
        while True:
            stdscr.clear()
            self.draw_letter_grid(stdscr)

            key = stdscr.getkey()
            if len(key) == 1 and key in self.letters:
                if current_character_index > 4: continue
                self.letter_grid[self.guesses][current_character_index] = (key, 0)
                if current_character_index <= 4: current_character_index += 1
            elif key == "\n":
                if self.guesses > 5 or self.did_win:
                    return
                if current_character_index > 4:
                    self.did_win = self.process_current_guess()
                    current_character_index = 0
                    
            elif key == "KEY_BACKSPACE":

                if current_character_index <= 4: self.letter_grid[self.guesses][current_character_index] = (" ", 0)
                if current_character_index > 0:
                    self.letter_grid[self.guesses][current_character_index-1] = (" ", 0)
                    current_character_index -= 1
                    
                

            stdscr.refresh()