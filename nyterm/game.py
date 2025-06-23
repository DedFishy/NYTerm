import curses
import math
from const import COLORS
from connections import Connections
from wordle import Wordle
from strands import Strands
from mini import Mini
from spelling_bee import SpellingBee
from spelling_bee_loader import load_spelling_bee, loader
import util
import datetime
import os
from statman import StatManager

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

    STATMAN = StatManager()

    def __init__(self):
        self.OPTIONS = {
            "Spelling Bee": self.start_bee,
            "Mini": self.start_mini,
            "Strands": self.start_strands,
            "Connections": self.start_connections,
            "Wordle": self.start_wordle,
            "Stats": self.show_stats,
            "Quit": self.quit,
        }

        self.KEYS = {
            "KEY_DOWN": self.key_down,
            "KEY_UP": self.key_up,
            "\n": lambda: self.OPTIONS[list(self.OPTIONS.keys())[self.selected]](),
            "KEY_MOUSE": self.click_option
        }

        self.row_positions = {}

    def click_option(self):
        mouse_event = curses.getmouse()
        if mouse_event[4] != 2: return
        mouse_position = (mouse_event[1], mouse_event[2])
        func = None
        for candidate in self.row_positions.keys():
            if self.row_positions[candidate] == mouse_position[1]:
                func = self.OPTIONS[candidate]
                break
        if func: func()
        util._log(self.row_positions, func, candidate, mouse_event)

    def start_bee(self):
        puzzle = None
        load_spelling_bee()
        option = util.run_button_row(["Today's", "Yesterday's", "This Week", "Last Week", "Cancel"], self.stdscr, 0, "Select Spelling Bee Day")
        if option == "Today's":
            puzzle = loader.game_data["today"]
        elif option == "Yesterday's":
            puzzle = loader.game_data["yesterday"]
        elif option == "This Week":
            puzzle_options = {puzzle["displayWeekday"]: puzzle for puzzle in loader.game_data["pastPuzzles"]["thisWeek"]}
            option = util.run_button_row(list(puzzle_options.keys()), self.stdscr, 0, "This Week's Puzzles")
            puzzle = puzzle_options[option]
        elif option == "Last Week":
            puzzle_options = {puzzle["displayWeekday"]: puzzle for puzzle in loader.game_data["pastPuzzles"]["lastWeek"]}
            option = util.run_button_row(list(puzzle_options.keys()), self.stdscr, 0, "Last Week's Puzzles")
            puzzle = puzzle_options[option]

        completion_ratio = SpellingBee(puzzle).start(self.stdscr)
        self.STATMAN.add_spelling_bee(completion_ratio)

    def start_wordle(self):
        do_start = self.select_ymd("Wordle")
        if do_start:
            wordle = Wordle(self.selected_year, self.selected_month, self.selected_day)
            if wordle.solution == None:
                util.show_dialog(self.stdscr, "Couldn't load that puzzle.")
                return
            won, attempts = wordle.start(self.stdscr)
            self.STATMAN.add_wordle(won, attempts)
    def start_connections(self):
        do_start = self.select_ymd("Connections")
        if do_start:
            connections = Connections(self.selected_year, self.selected_month, self.selected_day)
            if connections.solution == None or connections.solution == []:
                util.show_dialog(self.stdscr, "Couldn't load that puzzle.")
                return
            won, categories_completed = connections.start(self.stdscr)
            self.STATMAN.add_connections_game(won, categories_completed)
    def start_strands(self):
        do_start = self.select_ymd("Strands")
        if do_start:
            strands = Strands(self.selected_year, self.selected_month, self.selected_day)
            if strands.board == None or strands.board == []:
                util.show_dialog(self.stdscr, "Couldn't load that puzzle.")
                return
            completed, hints_used = strands.start(self.stdscr)
            self.STATMAN.add_strands(completed, hints_used)
    
    def start_mini(self):
        mini = Mini()
        completed, time = mini.start(self.stdscr)
        self.STATMAN.add_mini(completed, time)

    def show_stats(self):
        selected = 0
        stat_options = ["Spelling Bee", "Mini", "Connections", "Strands", "Wordle"]
        while True:
            self.stdscr.clear()

            rows = [
                [(" " + x + " ", (COLORS["SELECTED_OPTION"] if stat_options.index(x) == selected else COLORS["UNSELECTED_OPTION"])) for x in stat_options]
            ]
            
            selected_name = stat_options[selected]

            if selected_name == "Spelling Bee":
                rows.append((f"Games Played: {self.STATMAN.spelling_bee["gamesPlayed"]}", 0))
                rows.append((f"Average Completion: {round(util.get_average(self.STATMAN.spelling_bee["gameCompletion"]), 2)}", 0))
            elif selected_name == "Mini":
                rows.append((f"Games Played: {self.STATMAN.mini["gamesPlayed"]}", 0))
                rows.append((f"Games Completed: {self.STATMAN.mini["gamesCompleted"]}", 0))
                rows.append((f"Average Time: {round(util.get_average(self.STATMAN.mini["gameTimes"]), 2)}", 0))
            elif selected_name == "Connections":
                rows.append((f"Games Played: {self.STATMAN.connections["gamesPlayed"]}", 0))
                rows.append((f"Games Won: {self.STATMAN.connections["gamesWon"]}", 0))
                rows.append((f"Games Lost: {self.STATMAN.connections["gamesLost"]}", 0))
                rows.append((f"Average Categories Completed: {round(util.get_average(self.STATMAN.connections["categoriesCompleted"]), 2)}", 0))
            elif selected_name == "Strands":
                rows.append((f"Games Played: {self.STATMAN.strands["gamesPlayed"]}", 0))
                rows.append((f"Games Completed: {self.STATMAN.strands["gamesCompleted"]}", 0))
                rows.append((f"Average Hints Used: {round(util.get_average(self.STATMAN.strands["hintsUsed"]), 2)}", 0))
            elif selected_name == "Wordle":
                rows.append((f"Games Played: {self.STATMAN.wordle["gamesPlayed"]}", 0))
                rows.append((f"Games Won: {self.STATMAN.wordle["gamesWon"]}", 0))
                rows.append((f"Games Lost: {self.STATMAN.wordle["gamesLost"]}", 0))
                rows.append((f"Average # of Attempts: {round(util.get_average(self.STATMAN.wordle["attempts"]), 2)}", 0))


            util.render_rows_to_center(rows, self.stdscr)

            key = self.stdscr.getkey()

            if key == "KEY_LEFT":
                if selected > 0:
                    selected -= 1
            elif key == "KEY_RIGHT":
                if selected < len(stat_options) - 1:
                    selected += 1
            elif key == "\n" or key == "":
                break

            self.stdscr.refresh()

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
        input_values, result = util.run_row_selector(inputs, self.stdscr, 3, f"Select date to play {game_title}")
        self.selected_year = input_values["Year"]
        self.selected_month = input_values["Month"]
        self.selected_day = input_values["Day"]
        return result

    def render(self):
        self.stdscr.clear()
        rows_to_render = [
            ("▄▄▄▄▄▄▄▄▄▄", 0),
            [(" █    ", 0), ("███", COLORS["YELLOW"]), ("█", COLORS["BLUE"]), ("█", 0)],
            [(" █", 0), ("█", COLORS["BLUE"]), ("███", COLORS["GREEN"]), (" >  █", 0)],
            [(" █ ", 0), ("███", COLORS["YELLOW"]), ("  ▔ █", 0)],
            ("▀▀▀▀▀▀▀▀▀▀", 0),
            ("NYTerminal", COLORS["TITLE"]), 
            ("The (good) NYT games implemented in the terminal.", COLORS["SUBTITLE"]), 
            ("By Boyne Gregg", COLORS["SUBTITLE"]),
            ("[UP/DOWN/LEFT/RIGHT] Move             ", COLORS["PURPLE"]),
            ("               [ESC] Menu             ", COLORS["PURPLE"]),
            ("               [TAB] Hint             ", COLORS["PURPLE"]),
            ("             [SPACE] Select           ", COLORS["PURPLE"]),
            ("             [ENTER] Submit           ", COLORS["PURPLE"]),
            ("            [CTRL+C] Exit             ", COLORS["PURPLE"]),
            ]
        i = 0
        for option in self.OPTIONS.keys():
            if i == self.selected: rows_to_render.append((option, COLORS["SELECTED_OPTION"], option))
            else: rows_to_render.append((option, COLORS["UNSELECTED_OPTION"], option))
            i += 1

        self.row_positions = util.render_rows_to_center(rows_to_render, self.stdscr)
        

    def start(self, stdscr: curses.window):
        
        self.STATMAN.load_from_file()

        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_RED, curses.COLOR_WHITE)

        

        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)

        curses.curs_set(False)
        
        self.stdscr = stdscr
        while self.running:
            self.render()
            key = self.stdscr.getkey()
            if key in self.KEYS.keys():
                self.KEYS[key]()
        

def run():
    os.environ.setdefault('ESCDELAY', '0')

    game = Game()
    
    try:
        curses.wrapper(game.start)
    except KeyboardInterrupt:
        pass
    finally:
        game.STATMAN.save_to_file()
