import curses
import math
import util
from datetime import datetime
from curses import window
from const import COLORS
from importlib import resources as impresources
import word_lists
from bisect import bisect_left

class Connections:
    BASE_URL = "https://www.nytimes.com/svc/connections/v2/"
    TILE_WIDTH = 14
    TILE_HEIGHT = 3

    year = None
    month = None
    day = None
    game_data = None

    selected_x = 0
    selected_y = 0
    selected_coords = []

    guesses_left = 4

    solution = []
    solved = [] # Contains index of each solved category (in order)

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
        self.solved = []
        self.already_guessed = []
        self.load()

    def get_from_date(self, date: datetime):
        return Connections(date.year, date.month, date.day)

    def get_url_for_date(self):
        return self.BASE_URL + "/" + util.get_file_name_for_date(self.year, self.month, self.day)
    
    def load(self):
        self.game_data = util.load_json_from_url(self.get_url_for_date())
        if self.game_data != None:
            self.solution = self.game_data["categories"]

    def construct_word_tile(self, word):
        inner_width = self.TILE_WIDTH-2
        word = str(word) # TODO
        if len(word) > inner_width:
            word = word[0:(inner_width-3)] + "..."
        top = f"┌{"─"*inner_width}┐"
        middle = "│" + str(word).center(inner_width) + "│"
        bottom = f"└{"─"*inner_width}┘"
        return top, middle, bottom
    
    def construct_category_tile(self, title: str, words: list[str]):
        inner_width = self.TILE_WIDTH*4-2
        middle_text = ", ".join(words)
        if len(title) > inner_width:
            title = title[0:(inner_width-3)] + "..."
        top = f"┌{title.center(inner_width, "─")}┐"
        middle = "│" + str(middle_text).center(inner_width) + "│"
        bottom = f"└{"─"*inner_width}┘"
        return top, middle, bottom
    
    def construct_game_matrix(self):
        # If we just lost, reveal all answers
        if self.guesses_left <= 0:
            for category in range(4):
                if category not in self.solved:
                    self.solved.append(category)

        matrix = [[None for _ in range(4)] for _ in range(4)]
        tiles_to_display = self.solution.copy()
        
        current_row = 0
        for category in self.solved:
            matrix[current_row] = (tiles_to_display[category]["title"], [x["content"] for x in tiles_to_display[category]["cards"]], category)
            tiles_to_display[category] = None
            current_row+=1

        for category in tiles_to_display: # Iterate through remaining categories
            if category == None: continue
            for tile in category["cards"]:
                pos_y = math.floor(tile["position"] / 4)
                pos_x = tile["position"] % 4
                if type(matrix[pos_y]) != tuple and matrix[pos_y][pos_x] == None:
                        matrix[pos_y][pos_x] = tile["content"]
                else:
                    # Find first blank space
                    found_space = False
                    for y in range(len(self.solved), 4):
                        for x in range(4):
                            if matrix[y][x] == None:
                                matrix[y][x] = tile["content"]
                                found_space = True
                                break
                        if found_space: break
        return matrix
        
    
    def draw_grid(self, stdscr: window):
        self.selected_items = []
        start_coord_yx = util.get_starting_dimensions_yx(self.TILE_WIDTH * 4, self.TILE_HEIGHT * 4, stdscr.getmaxyx())
        y = start_coord_yx[0]
        matrix = self.construct_game_matrix()
        max_y = 3 - len(self.solved)

        if self.selected_y > max_y: self.selected_y = max_y
        elif self.selected_y < 0: self.selected_y = 0
        if self.selected_x > 3: self.selected_x = 3
        if self.selected_x < 0: self.selected_x = 0

        current_tile_x = 0
        current_tile_y = 0

        message = None
        if self.did_win:
            message = "Congratulations!"
        elif self.guesses_left <= 0:
            message = "Too bad!"
            
        else:
            message = f"Mistakes Remaining: {"•"*self.guesses_left}"

        for row in matrix:
            x = start_coord_yx[1]
            if type(row) == tuple:
                title = row[0]
                words = row[1]
                color_pair = curses.color_pair(self.category_colors[row[2]])
                tile = self.construct_category_tile(title, words)
                stdscr.addstr(y+0, x, tile[0], color_pair)
                stdscr.addstr(y+1, x, tile[1], color_pair)
                stdscr.addstr(y+2, x, tile[2], color_pair)
            else:
                current_tile_x = 0
                for word in row:
                    word_tile = self.construct_word_tile(word)
                    selected = False
                    if (current_tile_x, current_tile_y) in self.selected_coords:
                        self.selected_items.append(word)
                        selected = True
                    
                    if current_tile_x == self.selected_x and current_tile_y == self.selected_y:
                        
                        if selected:
                            color_pair = curses.color_pair(COLORS["TOGGLED_SELECTED_OPTION"])
                        else:
                            color_pair = curses.color_pair(COLORS["SELECTED_OPTION"])
                    elif selected:
                        color_pair = curses.color_pair(COLORS["TOGGLED_OPTION"])
                    else:
                        color_pair = curses.color_pair(COLORS["UNSELECTED_OPTION"])

                    stdscr.addstr(y+0, x, word_tile[0], color_pair)
                    stdscr.addstr(y+1, x, word_tile[1], color_pair)
                    stdscr.addstr(y+2, x, word_tile[2], color_pair)
                    x+=self.TILE_WIDTH
                    current_tile_x+=1
                current_tile_y+=1
            y+=self.TILE_HEIGHT
        
        

        stdscr.addstr(y, start_coord_yx[1], message.center(self.TILE_WIDTH*4))
    
    def process_guess(self):
        i = 0
        for category in self.solution:
            is_valid = True
            for word in category["cards"]:
                if word["content"] not in self.selected_items:
                    is_valid = False
                    break
            if is_valid:
                return i
            i+=1
        return -1

    def start(self, stdscr: window):
        while True:
            stdscr.clear()
            self.draw_grid(stdscr)

            key = stdscr.getkey()
            if key == " ":
                coord = (self.selected_x, self.selected_y)
                if coord in self.selected_coords:
                    del self.selected_coords[self.selected_coords.index(coord)]
                else:
                    if len(self.selected_coords) <= 3:
                        self.selected_coords.append(coord)
                    
            elif key == "\n":
                if self.did_win or self.guesses_left <= 0: return
                if len(self.selected_coords) >= 3:
                    self.selected_coords = []
                    if self.selected_items in self.already_guessed or len(self.selected_items) < 4:
                        self.selected_items = []
                    else:
                        self.already_guessed.append(self.selected_items)
                        index = self.process_guess()
                        if index == -1:
                            self.guesses_left -= 1
                        else:
                            self.solved.append(index)
                            if len(self.solved) >= 4:
                                self.did_win = True
                        
            
            elif key == "KEY_LEFT":
                self.selected_x -= 1
            elif key == "KEY_RIGHT":
                self.selected_x += 1
            elif key == "KEY_UP":
                self.selected_y -= 1
            elif key == "KEY_DOWN":
                self.selected_y += 1
            stdscr.refresh()