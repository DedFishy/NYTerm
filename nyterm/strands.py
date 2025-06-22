import curses
import math
import random
import util
from datetime import datetime
from curses import window
from const import COLORS, STRANDS_LETTER_DIRECTIONS
from importlib import resources as impresources
import word_lists
from bisect import bisect_left

class Strands:
    BASE_URL = "https://www.nytimes.com/svc/strands/v2/"
    LETTER_WIDTH = 5
    LETTER_HEIGHT = 3

    year = None
    month = None
    day = None
    game_data = None

    selected_x = 0
    selected_y = 0
    selected_coords = []

    board = []
    valid_words = []
    theme_words = []
    theme_coords = {}
    clue = ""
    guessed_theme_words = []
    guessed_theme_words_coords = []

    hints = 0
    current_hint_progress = 0

    current_hint_coords = []
    target_hint_word = ""
    show_current_hint_order = False

    hint_progress_chars = {
        0: " ",
        1: "▃",
        2: "▅",
        3: "█"
    }

    selected_items = []

    already_guessed = []

    category_colors = {
        0: COLORS["YELLOW"],
        1: COLORS["GREEN"],
        2: COLORS["BLUE"],
        3: COLORS["PURPLE"]
    }

    def __init__(self, year, month, day):
        self.year = str(year)
        self.month = str(month)
        self.day = str(day)
        self.guesses_left = 4
        self.did_win = False
        self.selected_x = 0
        self.selected_y = 0
        self.selected_coords = []
        self.already_guessed = []
        self.guessed_theme_words = []
        self.guessed_theme_words_coords = []
        self.hints = 0
        self.current_hint_progress = 0
        self.load()

    def get_from_date(self, date: datetime):
        return Strands(date.year, date.month, date.day)

    def get_url_for_date(self):
        return self.BASE_URL + "/" + util.get_file_name_for_date(self.year, self.month, self.day)
    
    def load(self):
        self.game_data = util.load_json_from_url(self.get_url_for_date())
        if self.game_data != None:
            self.board = self.game_data["startingBoard"]
            self.valid_words = self.game_data["solutions"]
            self.theme_words = self.game_data["themeWords"]
            self.theme_words.append(self.game_data["spangram"])
            self.theme_coords = self.game_data["themeCoords"]
            self.theme_coords[self.game_data["spangram"]] = self.game_data["spangramCoords"]
            self.clue = self.game_data["clue"]

    def construct_letter(self, letter, directions = None):
        top = f"{"╲" if STRANDS_LETTER_DIRECTIONS.TOP_LEFT in directions else "╭"}─{"│" if STRANDS_LETTER_DIRECTIONS.TOP in directions else "─"}─{"╱" if STRANDS_LETTER_DIRECTIONS.TOP_RIGHT in directions else "╮"}"
        middle = f"{"─" if STRANDS_LETTER_DIRECTIONS.LEFT in directions else "│"} {letter} {"─" if STRANDS_LETTER_DIRECTIONS.RIGHT in directions else "│"}"
        bottom = f"{"╱" if STRANDS_LETTER_DIRECTIONS.BOTTOM_LEFT in directions else "╰"}─{"│" if STRANDS_LETTER_DIRECTIONS.BOTTOM in directions else "─"}─{"╲" if STRANDS_LETTER_DIRECTIONS.BOTTOM_RIGHT in directions else "╯"}"
        return top, middle, bottom
    
    def get_direction(self, coord_one, coord_two):
        # Next tile is to the right
        if coord_two[0] > coord_one[0]:
            # Next tile is below
            if coord_two[1] > coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.BOTTOM_RIGHT
            # Next tile is above
            elif coord_two[1] < coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.TOP_RIGHT
            # Next tile is on same level
            else:
                direction = STRANDS_LETTER_DIRECTIONS.RIGHT
        # Next tile is to the left
        elif coord_two[0] < coord_one[0]:
            # Next tile is below
            if coord_two[1] > coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.BOTTOM_LEFT
            # Next tile is above
            elif coord_two[1] < coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.TOP_LEFT
            # Next tile is on same level
            else:
                direction = STRANDS_LETTER_DIRECTIONS.LEFT
        # Next tile is in same column
        else:
            # Next tile is below
            if coord_two[1] > coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.BOTTOM
            # Next tile is above
            elif coord_two[1] < coord_one[1]:
                direction = STRANDS_LETTER_DIRECTIONS.TOP
            # Next tile is on same level
            else:
                direction = False # Should never happen!
        return direction
    
    def draw_grid(self, stdscr: window):
        self.selected_items = []
        start_coord_yx = util.get_starting_dimensions_yx(self.LETTER_WIDTH * len(self.board[0]), self.LETTER_HEIGHT * len(self.board), stdscr.getmaxyx())
        y = start_coord_yx[0]
        max_y = len(self.board)-1
        max_x = len(self.board[0])-1

        if self.selected_y > max_y: self.selected_y = max_y
        elif self.selected_y < 0: self.selected_y = 0
        if self.selected_x > max_x: self.selected_x = max_x
        if self.selected_x < 0: self.selected_x = 0

        current_letter_x = 0
        current_letter_y = 0

        message = None
        if self.did_win:
            message = "Congratulations!"
            
        else:
            message = f"Theme: {self.clue} | Hints: {self.hint_progress_chars[3]*self.hints}{self.hint_progress_chars[self.current_hint_progress]} [TAB to use]"

        for row in self.board:
            x = start_coord_yx[1]
            current_letter_x = 0
            for letter in row:
                directions = []
                try:
                    selected_index = self.selected_coords.index((current_letter_x, current_letter_y))
                except ValueError: selected_index = -1

                try:
                    theme_words_index = self.guessed_theme_words_coords.index([current_letter_x, current_letter_y])
                except ValueError: theme_words_index = -1

                try:
                    hint_word_index = self.current_hint_coords.index([current_letter_y, current_letter_x])
                except ValueError: hint_word_index = -1

                is_in_theme_word = False
                is_in_hint_word = False

                next_tile_coords = None
                previous_tile_coords = None
                if selected_index != -1:
                    if selected_index < len(self.selected_coords)-1:
                        next_tile_coords = self.selected_coords[selected_index+1]
                    if selected_index > 0:
                        previous_tile_coords = self.selected_coords[selected_index-1]
                elif theme_words_index != -1:
                    is_in_theme_word = True
                    if theme_words_index < len(self.guessed_theme_words_coords)-1:
                        next_tile_coords = self.guessed_theme_words_coords[theme_words_index+1]
                    if theme_words_index > 0:
                        previous_tile_coords = self.guessed_theme_words_coords[theme_words_index-1]
                elif hint_word_index != -1:
                    is_in_hint_word = True
                    if self.show_current_hint_order:
                        if hint_word_index < len(self.current_hint_coords)-1:
                            next_tile_coords = self.current_hint_coords[hint_word_index+1].copy()
                            next_tile_coords.reverse()
                        if hint_word_index > 0:
                            previous_tile_coords = self.current_hint_coords[hint_word_index-1].copy()
                            previous_tile_coords.reverse()

                if next_tile_coords != None: directions.append(self.get_direction((current_letter_x, current_letter_y), next_tile_coords))
                if previous_tile_coords != None: directions.append(self.get_direction((current_letter_x, current_letter_y), previous_tile_coords))


                word_tile = self.construct_letter(letter, directions)
                selected = False
                if (current_letter_x, current_letter_y) in self.selected_coords:
                    self.selected_items.append(letter)
                    selected = True
                
                if current_letter_x == self.selected_x and current_letter_y == self.selected_y:
                    
                    if selected:
                        color_pair = curses.color_pair(COLORS["TOGGLED_SELECTED_OPTION"])
                    else:
                        color_pair = curses.color_pair(COLORS["SELECTED_OPTION"])
                elif selected:
                    color_pair = curses.color_pair(COLORS["TOGGLED_OPTION"])
                elif is_in_theme_word:
                    color_pair = curses.color_pair(COLORS["BLUE"])
                elif is_in_hint_word:
                    color_pair = curses.color_pair(COLORS["GREEN"])
                else:
                    color_pair = curses.color_pair(COLORS["UNSELECTED_OPTION"])

                stdscr.addstr(y+0, x, word_tile[0], color_pair)
                stdscr.addstr(y+1, x, word_tile[1], color_pair)
                stdscr.addstr(y+2, x, word_tile[2], color_pair)
                x+=self.LETTER_WIDTH
                current_letter_x+=1
            current_letter_y+=1
            y+=self.LETTER_HEIGHT
        
        

        stdscr.addstr(y, start_coord_yx[1], message.center(self.LETTER_WIDTH*len(self.board[0])))
    
    def process_guess(self):
        formed_word = ""
        for coord in self.selected_coords:
            formed_word += self.board[coord[1]][coord[0]]
        if formed_word in self.theme_words and not formed_word in self.already_guessed:
            is_correct_theme_word = True
            i = 0
            for coord in self.theme_coords[formed_word]:
                if not coord[0] == self.selected_coords[i][0] and coord[1] == self.selected_coords[i][1]:
                    is_correct_theme_word = False
                i += 1
            if is_correct_theme_word:
                if self.target_hint_word == formed_word:
                    self.target_hint_word = ""
                    self.current_hint_coords = []
                    self.show_current_hint_order = False
                self.already_guessed.append(formed_word)
                self.guessed_theme_words.append(formed_word)
                new_coords = self.theme_coords[formed_word].copy()
                for coord in new_coords: coord.reverse()
                self.guessed_theme_words_coords.extend(new_coords)
                self.guessed_theme_words_coords.append(None) # Separator between word connections
                
        elif formed_word not in self.already_guessed and self.valid_words[bisect_left(self.valid_words, formed_word)] == formed_word:
            self.already_guessed.append(formed_word)
            self.current_hint_progress+=1
            if self.current_hint_progress >= 3:
                self.hints+=1
                self.current_hint_progress=0
        
        self.selected_coords = []

        if len(self.guessed_theme_words) >= len(self.theme_words):
            
            self.did_win = True
    
    def use_hint(self):
        if self.hints > 0:
            self.hints -= 1
        else:
            return
        candidate_words = self.theme_words.copy()
        for word in self.already_guessed:
            try: candidate_words.remove(word)
            except ValueError: pass
        if self.current_hint_coords:
            if not self.show_current_hint_order:
                self.show_current_hint_order = True
            else:
                self.hints += 1
        else:
            self.target_hint_word = random.choice(candidate_words)
            self.current_hint_coords = self.theme_coords[self.target_hint_word]

    def start(self, stdscr: window):
        while True:
            stdscr.clear()
            self.draw_grid(stdscr)

            key = stdscr.getkey()
            if key == " ":
                coord = (self.selected_x, self.selected_y)
                if coord in self.selected_coords:
                    if self.selected_coords[-1] == coord:
                        del self.selected_coords[self.selected_coords.index(coord)]
                    else:
                        self.selected_coords = []
                else:
                    if len(self.selected_coords) <= 0 or (abs(coord[0]-self.selected_coords[-1][0]) <= 1 and abs(coord[1]-self.selected_coords[-1][1]) <= 1):
                        self.selected_coords.append(coord)
                    else:
                        self.selected_coords = []
                    
            elif key == "\n":
                if self.did_win: return
                self.process_guess()
            
            elif key == "\t":
                self.use_hint()
            
            elif key == "KEY_LEFT":
                self.selected_x -= 1
            elif key == "KEY_RIGHT":
                self.selected_x += 1
            elif key == "KEY_UP":
                self.selected_y -= 1
            elif key == "KEY_DOWN":
                self.selected_y += 1
            stdscr.refresh()