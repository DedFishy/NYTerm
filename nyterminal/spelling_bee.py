import curses
import nyterminal.util as util
from datetime import datetime
from curses import window
from nyterminal.const import COLORS
from importlib import resources as impresources
from bisect import bisect_left
from nyterminal.spelling_bee_loader import load_spelling_bee

class SpellingBee:

    game_data = None

    progress = 0

    did_win = False
    letters = ""

    allowed_words = []
    pangrams = []

    guessed = []

    max_points = 0

    typed_word = ""

    ranks = {
        0.02: "Good Start",
        0.05: "Moving Up",
        0.08: "Good",
        0.15: "Solid",
        0.25: "Nice",
        0.4: "Great",
        0.5: "Amazing",
        0.7: "Genius",
        1.0: "Queen Bee"
    }

    solution = None
    def __init__(self, game_data):
        self.did_win = False
        self.game_data = game_data
        self.load()
    
    def load(self):
        if self.game_data != None:
            self.letters = self.game_data["validLetters"]
            self.allowed_words = self.game_data["answers"]
            self.pangrams = self.game_data["pangrams"]

            self.progress = 0

            for word in self.allowed_words:
                self.max_points += self.get_score_for_word(word)

            self.allowed_words.sort() # THEY PUT THE PANGRAMS IN THE WRONG SPOT!!!!
    
    def get_rank_for_percentage(self, percentage):
        found_rank = "Beginner"
        for rank in self.ranks.keys():
            if rank <= percentage:
                found_rank = self.ranks[rank]
            else:
                break
        return found_rank
    
    def draw_letter_hexagon(self, stdscr: window):
        
        letters = [x.upper() for x in self.letters]
        
        a,b,c,d,e,f,g = letters
        
        display = rf"""
----╔═══╗
╔═══╣ b ╠═══╗
║ g ╠═══╣ c ║
╠═══╣ a ╠═══╣
║ f ╠═══╣ d ║
╚═══╣ e ╠═══╝
----╚═══╝
"""
        
        display = display.replace("a", a).replace("b", b).replace("c", c).replace("d", d).replace("e", e).replace("f", f).replace("g", g)
        rows = [(self.typed_word.upper() if self.typed_word != "" else "Start typing...", 0)]
        rows.extend((x.replace("-", ""), COLORS["YELLOW"]) for x in display.splitlines())
        util.render_rows_to_center(rows, stdscr)

        width = len(max(x[0] for x in rows))
        height = len(rows) + 1
        start_coord_yx = util.get_starting_dimensions_yx(width, height, stdscr.getmaxyx())

        
    
        util.addstr(stdscr, start_coord_yx[0] + height + 1, start_coord_yx[1], f"{self.get_rank_for_percentage(self.progress/self.max_points)} - {self.progress}".center(width))
        if self.did_win:
            util.addstr(stdscr, start_coord_yx[0] + height + 2, start_coord_yx[1], f"Found them all!".center(width))

    def is_guess_in_word_list(self):
        index = bisect_left(self.allowed_words, self.typed_word)
        if len(self.allowed_words) > 0:
            return self.allowed_words[index] == self.typed_word
        return False
    
    def get_score_for_word(self, word):
        score = len(word)
        if score == 4: score = 1
        if word in self.pangrams: score += 7
        return score
    

    def start(self, stdscr: window):
        while True:
            stdscr.clear()
            self.draw_letter_hexagon(stdscr)

            key = stdscr.getkey()
            if len(key) == 1 and key in self.letters:
                self.typed_word += key
            elif key == "\n":
                
                if self.did_win: break
                
                if self.is_guess_in_word_list():
                    if not self.typed_word in self.guessed:
                    
                        self.progress += self.get_score_for_word(self.typed_word)
                        self.guessed.append(self.typed_word)

                        if len(self.guessed) == len(self.allowed_words):
                            self.did_win = True
                    else:
                        util.show_dialog(stdscr, "You have already used that.")
                else:
                    util.show_dialog(stdscr, "That is not a valid word.")
                
                self.typed_word = ""



            elif key == "KEY_BACKSPACE":

                self.typed_word = self.typed_word[:-1]
                    
            elif key == "":
                break

            stdscr.refresh()

        return self.progress / self.max_points