import curses
import math
import util
from curses import window
from const import COLORS
import time


class Mini:
    BASE_URL = "https://www.nytimes.com/svc/crosswords/v6/puzzle/mini.json"
    LETTER_WIDTH = 5
    LETTER_HEIGHT = 3

    game_data = None

    did_win = False
    letters = "abcdefghijklmnopqrstuvwxyz"

    cells = []
    cell_answers = {}
    width = 0
    height = 0
    start_time = 0
    clues_across = {}
    clues_down = {}

    selected_cell = -1

    is_direction_across = True

    def __init__(self):
        self.did_win = False
        self.selected_cell = -1
        self.load()
    
    def load(self):
        self.game_data = util.load_json_from_url(self.BASE_URL)
        if self.game_data != None:
            self.game_data = self.game_data["body"][0]
            self.cells = self.game_data["cells"]
            self.width = self.game_data["dimensions"]["width"]
            self.height = self.game_data["dimensions"]["height"]
            self.cell_answers = {}
            i = 0
            for cell in self.cells:
                if len(cell.keys()) > 0:
                    if self.selected_cell == -1:
                        self.selected_cell = i
                    self.cell_answers[i] = " "
                i+=1
            
            self.clues_across = {}
            self.clues_down = {}
            for clue in self.game_data["clues"]:
                if clue["direction"] == "Across":
                    for cell in clue["cells"]:
                        self.clues_across[cell] = clue["label"] + ": " + clue["text"][0]["plain"]
            for clue in self.game_data["clues"]:
                if clue["direction"] == "Down":
                    for cell in clue["cells"]:
                        self.clues_down[cell] = clue["label"] + ": " + clue["text"][0]["plain"]

    def construct_letter_tile(self, number, letter):
        top = f"{number}───┐"
        middle = "│ " + str(letter).upper() + " │"
        bottom = "└───┘"
        return top, middle, bottom
    def construct_blocked_tile(self):
        return "█████", "█████", "█████"
    
    def draw_letter_grid(self, stdscr: window):
        start_coord_yx = util.get_starting_dimensions_yx(self.LETTER_WIDTH * self.width, self.LETTER_HEIGHT * self.height, stdscr.getmaxyx())
        
        i = 0
        for cell in self.cells:
            
            y = start_coord_yx[0] + math.floor(i/self.width)*self.LETTER_HEIGHT
            x = start_coord_yx[1] + (i % self.height)*self.LETTER_WIDTH

            if len(self.cells[i].keys()) > 0:
                is_block = False
                letter_tile = self.construct_letter_tile(cell["label"] if "label" in cell.keys() else "┌", self.cell_answers[i])
            else:
                is_block = True
                letter_tile = self.construct_blocked_tile()

            if i == self.selected_cell:
                color = COLORS["SELECTED_OPTION"]
            elif (
                (self.is_direction_across and math.floor(i/self.width) == math.floor(self.selected_cell/self.width)) or
                (not self.is_direction_across and i % self.width == self.selected_cell % self.width) 
            ) and not is_block:
                color = COLORS["BLUE"]

            else:
                color = 0
            color_pair = curses.color_pair(color)

            util.addstr(stdscr, y+0, x, letter_tile[0], color_pair)
            util.addstr(stdscr, y+1, x, letter_tile[1], color_pair)
            util.addstr(stdscr, y+2, x, letter_tile[2], color_pair)
            i += 1
        
        message = None
        if self.did_win:
            message = f"You solved the Mini in {int(time.time()-self.start_time)} seconds!"
        else:
            message = f"{'Across' if self.is_direction_across else 'Down'} " + (self.clues_across if self.is_direction_across else self.clues_down)[self.selected_cell]
        util.addstr(stdscr, start_coord_yx[0] + self.width*self.LETTER_HEIGHT, start_coord_yx[1], message.center(self.LETTER_WIDTH*5))

    
    def start(self, stdscr: window):
        self.start_time = time.time()
        current_character_index = 0
        while True:
            stdscr.clear()
            self.draw_letter_grid(stdscr)

            key = stdscr.getkey()
            if len(key) == 1 and key in self.letters:
                self.cell_answers[self.selected_cell] = key
                new_pos = self.selected_cell + (1 if self.is_direction_across else self.width)
                if new_pos in self.cell_answers.keys():
                    self.selected_cell = new_pos
                
                valid = True
                for answer in self.cell_answers.keys():
                    if self.cell_answers[answer].upper() != self.cells[answer]["answer"].upper():
                        valid = False
                        break
                if valid:
                    self.did_win = True
                    self.selected_cell = -1
            
            elif key == "\n":
                if self.did_win:
                    break

            elif key == "KEY_BACKSPACE":

                self.cell_answers[self.selected_cell] = " "
                new_pos = self.selected_cell - (1 if self.is_direction_across else self.width)
                if new_pos in self.cell_answers.keys():
                    self.selected_cell = new_pos
                    self.cell_answers[self.selected_cell] = " "

            elif key == "KEY_UP":
                if self.is_direction_across:
                    self.is_direction_across = False
                else:
                    new_pos = self.selected_cell - self.width
                    if new_pos in self.cell_answers.keys():
                        self.selected_cell = new_pos
            elif key == "KEY_DOWN":
                if self.is_direction_across:
                    self.is_direction_across = False
                else:
                    new_pos = self.selected_cell + self.width
                    if new_pos in self.cell_answers.keys():
                        self.selected_cell = new_pos
            elif key == "KEY_LEFT":
                if self.is_direction_across:
                    new_pos = self.selected_cell - 1
                    if new_pos in self.cell_answers.keys():
                        self.selected_cell = new_pos
                else:
                    self.is_direction_across = True
            elif key == "KEY_RIGHT":
                if self.is_direction_across:
                    new_pos = self.selected_cell + 1
                    if new_pos in self.cell_answers.keys():
                        self.selected_cell = new_pos
                else:
                    self.is_direction_across = True   
                

            stdscr.refresh()