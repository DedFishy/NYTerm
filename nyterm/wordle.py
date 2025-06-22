import curses
import util
from datetime import datetime
from curses import window
from const import COLORS
from importlib import resources as impresources
import word_lists
from bisect import bisect_left

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
    letter_statuses = {} # -1=unknown, 0=gray, 1=yellow, 2=green
    letter_status_codes = {-1: COLORS["UNKNOWN"], 0: 0, 1: COLORS["YELLOW"], 2: COLORS["GREEN"]}
    letter_grid = []

    with (impresources.files(word_lists) / "wordle.txt").open("rt") as word_list_file:
        allowed_words = word_list_file.read().split("\n")

    solution = None
    def __init__(self, year, month, day):
        self.year = str(year)
        self.month = str(month)
        self.day = str(day)
        self.letter_grid = [[(" ", -1) for _ in range(5)] for _ in range(6)]
        self.guesses = 0
        self.did_win = False
        for letter in self.letters:
            self.letter_statuses[letter] = -1
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

                color_pair = curses.color_pair(self.letter_status_codes[color if color != -1 else 0])

                util.addstr(stdscr, y+0, x, letter_tile[0], color_pair)
                util.addstr(stdscr, y+1, x, letter_tile[1], color_pair)
                util.addstr(stdscr, y+2, x, letter_tile[2], color_pair)
                x+=self.LETTER_WIDTH
            y+=self.LETTER_HEIGHT
        
        message = None
        if self.did_win:
            message = "Congratulations!"
        elif self.guesses > 5:
            message = "Too bad! Solution: " + self.solution.upper()
        if message == None:
            alphabet_x = int(stdscr.getmaxyx()[1]/2)-(26/2)
            for letter in self.letter_statuses.keys():
                util.addstr(stdscr, y, int(alphabet_x), letter.upper(), curses.color_pair(self.letter_status_codes[self.letter_statuses[letter]]) | curses.A_BOLD)
                alphabet_x += 1
        else:
            util.addstr(stdscr, y, start_coord_yx[1], message.center(self.LETTER_WIDTH*5))

    def is_guess_in_word_list(self):
        current_guess = "".join([x[0] for x in self.letter_grid[self.guesses]])
        index = bisect_left(self.allowed_words, current_guess)
        if len(self.allowed_words) > 0:
            return self.allowed_words[index] == current_guess
        return False

    def process_current_guess(self, stdscr):
        current_guess = [x[0] for x in self.letter_grid[self.guesses]]
        if not self.is_guess_in_word_list():
            util.show_dialog(stdscr, "That is not a valid word.")
            return None
        solution = list(self.solution)
        colors = [0,0,0,0,0]

        # Process Green
        for i in range(0, 5):
            if current_guess[i] == solution[i]:
                self.letter_statuses[current_guess[i]] = 2
                colors[i] = 2
                current_guess[i] = " "
                solution[i] = " "
        # Process Yellow
        for i in range(0, 5):
            if current_guess[i] != " ":
                if self.letter_statuses[current_guess[i]] != 2: # Don't overwrite green!
                    if current_guess[i] in solution:
                        
                        self.letter_statuses[current_guess[i]] = 1
                        colors[i] = 1
                        solution[solution.index(current_guess[i])] = " "
                        current_guess[i] = " "
                    else:
                        self.letter_statuses[current_guess[i]] = 0
                        colors[i] = 0
                        current_guess[i] = " "
                
        
        for i in range(0, 5):
            old_tup = self.letter_grid[self.guesses][i]
            self.letter_grid[self.guesses][i] = (old_tup[0], colors[i])

        self.guesses += 1
        return colors.count(2) == len(colors)

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
                    break
                if current_character_index > 4:
                    self.did_win = self.process_current_guess(stdscr)
                    if self.did_win == None:
                        self.letter_grid[self.guesses] = [(" ", 0) for _ in range(5)]
                    current_character_index = 0
                else:
                    util.show_dialog(stdscr, "You need to fill the row with letters.")

            elif key == "KEY_BACKSPACE":

                if current_character_index <= 4: self.letter_grid[self.guesses][current_character_index] = (" ", 0)
                if current_character_index > 0:
                    self.letter_grid[self.guesses][current_character_index-1] = (" ", 0)
                    current_character_index -= 1
                    
            elif key == "":
                break

            stdscr.refresh()
        return self.did_win, self.guesses
        