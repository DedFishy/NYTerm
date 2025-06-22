import curses
import util
from datetime import datetime
from curses import window
from const import COLORS
from importlib import resources as impresources
import word_lists
from bisect import bisect_left
from spelling_bee_loader import load_spelling_bee

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
    def __init__(self):
        self.did_win = False
        self.load()
    
    def load(self):
        self.game_data = load_spelling_bee()["today"]
        if self.game_data != None:
            self.letters = self.game_data["validLetters"]
            self.allowed_words = self.game_data["answers"]
            self.pangrams = self.game_data["pangrams"]

            for word in self.allowed_words:
                self.max_points += self.get_score_for_word(word)

            self.allowed_words.sort() # THEY PUT THE PANGRAMS IN THE WRONG SPOT!!!!
    
    def get_rank_for_percentage(self, percentage):
        found_rank = "?"
        for rank in self.ranks.keys():
            if rank < percentage:
                found_rank = self.ranks[rank]
            else:
                break
        return found_rank
    
    def draw_letter_hexagon(self, stdscr: window):
        start_coord_yx = util.get_starting_dimensions_yx(7, 5, stdscr.getmaxyx())
        a,b,c,d,e,f,g = self.letters
        rows = [
            
            (f"   {g}   ", 0),
            (f"{b}     {c}", 0),
            (f"   {a}   ", 0),
            (f"{d}     {f}", 0),
            (f"   {e}   ", 0)
        ]
        util.render_rows_to_center(rows, stdscr)
    
        util.addstr(stdscr, start_coord_yx[0] + 5, start_coord_yx[1], f"Score: {self.progress}".center(7))
        util.addstr(stdscr, start_coord_yx[0] + 6, start_coord_yx[1], f"Word: {self.typed_word}")
        util.addstr(stdscr, start_coord_yx[0] + 7, start_coord_yx[1], f"Rank: {self.get_rank_for_percentage(self.progress/self.max_points)}")
        if self.did_win:
            util.addstr(stdscr, start_coord_yx[0] + 8, start_coord_yx[1], f"You found every word!".center(7))

    def is_guess_in_word_list(self):
        index = bisect_left(self.allowed_words, self.typed_word)
        return self.allowed_words[index] == self.typed_word
    
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
                
                if self.did_win: return
                
                if self.is_guess_in_word_list() and not self.typed_word in self.guessed:
                    
                    self.progress += self.get_score_for_word(self.typed_word)
                    self.guessed.append(self.typed_word)

                    if len(self.guessed) == len(self.allowed_words):
                        self.did_win = True
                
                self.typed_word = ""



            elif key == "KEY_BACKSPACE":

                self.typed_word = self.typed_word[:-1]
                    
            elif key == "":
                return

            stdscr.refresh()