import curses
import enum

COLORS = {
    "TITLE": 1,
    "SUBTITLE": 2,
    "UNSELECTED_OPTION": 3,
    "SELECTED_OPTION": 4,
    "TOGGLED_OPTION": 7,
    "TOGGLED_SELECTED_OPTION": 8,
    "YELLOW": 2,
    "GREEN": 1,
    "BLUE": 5,
    "PURPLE": 6,
    "UNKNOWN": 4
}

class STRANDS_LETTER_DIRECTIONS(enum.Enum):
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    TOP = 4
    BOTTOM = 5
    LEFT = 6
    RIGHT = 7