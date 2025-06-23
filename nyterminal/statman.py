import json

import nyterminal.util as util
class StatManager:

    FILENAME = "nytermstats"

    connections = {
        "gamesPlayed": 0,
        "gamesWon": 0,
        "gamesLost": 0,
        "categoriesCompleted": []
    }
    mini = {
        "gamesPlayed": 0,
        "gamesCompleted": 0,
        "gameTimes": []
    }
    spelling_bee = {
        "gamesPlayed": 0,
        "gameCompletion": []
    }
    strands = {
        "gamesPlayed": 0,
        "gamesCompleted": 0,
        "hintsUsed": []
    }
    wordle = {
        "gamesPlayed": 0,
        "gamesWon": 0,
        "gamesLost": 0,
        "attempts": []
    }

    def __init__(self):
        pass

    def load_from_file(self):
        try:
            with open(self.FILENAME, 'x') as file:
                file.write("")
        except FileExistsError:
            pass
        with open(self.FILENAME, "r+") as file:
            file_content = file.read()
            if not file_content or file_content == "": return
            util._log(file_content)
            data = json.loads(file_content)
            self.connections = data["connections"]
            self.mini = data["mini"]
            self.spelling_bee = data["spelling_bee"]
            self.strands = data["strands"]
            self.wordle = data["wordle"]
    def save_to_file(self):
        with open(self.FILENAME, "w+") as file:
            file.write(json.dumps({
                "connections": self.connections,
                "mini": self.mini,
                "spelling_bee": self.spelling_bee,
                "strands": self.strands,
                "wordle": self.wordle
            }))
    
    def add_connections_game(self, won, categories_completed):
        self.connections["gamesPlayed"] += 1
        self.connections[f"games{'Won' if won else 'Lost'}"] += 1
        self.connections["categoriesCompleted"].append(categories_completed)

    def add_mini(self, completed, time):
        self.mini["gamesPlayed"] += 1
        if completed: self.mini["gamesCompleted"] += 1
        if time != 0: self.mini["gameTimes"].append(time)

    def add_spelling_bee(self, completion_ratio):
        self.spelling_bee["gamesPlayed"] += 1
        self.spelling_bee["gameCompletion"].append(completion_ratio)
    
    def add_strands(self, completed, hintsUsed):
        self.strands["gamesPlayed"] += 1
        if completed: self.strands["gamesCompleted"] += 1
        self.strands["hintsUsed"].append(hintsUsed)
    
    def add_wordle(self, won, attempts):
        self.wordle["gamesPlayed"] += 1
        self.wordle[f"games{'Won' if won else 'Lost'}"] += 1
        self.wordle["attempts"].append(attempts)