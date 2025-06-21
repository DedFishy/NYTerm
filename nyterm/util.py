import curses
import requests
from const import COLORS

def format_month(month):
    if len(month) < 2:
        return "0" + month
    return month

def format_day(day):
    if len(day) < 2:
        return "0" + day
    return day

def get_file_name_for_date(year, month, day):
    return f"{year}-{format_month(month)}-{format_day(day)}.json"

def load_json_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def render_rows_to_center(rows: dict[str, int], stdscr: curses.window):
    width = max((len(row) for row in rows))
    height = len(rows)
    y_coord, x_coord = stdscr.getmaxyx()
    y_coord /= 2
    x_coord /= 2
    y_coord -= height/2
    x_coord -= width/2

    y_coord = int(y_coord)
    x_coord = int(x_coord)

    for row in rows.keys():
        stdscr.addstr(y_coord, x_coord, row, curses.color_pair(rows[row]))
        y_coord += 1

def run_row_selector(inputs: dict[str, int|bool], stdscr: curses.window, default, title):
    
    inputs_keys = list(inputs.keys())
    selected = default
    still_selecting = True
    while still_selecting:
        stdscr.clear()
        row = []
        for input in inputs_keys:
            if input == inputs_keys[selected]:
                row.append(f"[{input.upper()}]" + (f": {inputs[input]}" if type(inputs[input]) == int else ""))
            else:
                row.append(input + (f": {inputs[input]}" if type(inputs[input]) == int else ""))
        render_rows_to_center({
            title:COLORS["SUBTITLE"], 
            " | ".join(row):COLORS["SELECTED_OPTION"]
        },
        stdscr)
        
        key = stdscr.getkey()
        if key == "KEY_LEFT" and selected > 0:
            selected -= 1
        elif key == "KEY_RIGHT" and selected < len(inputs_keys) - 1: 
            selected += 1
        elif key == "KEY_UP":
            if type(inputs[inputs_keys[selected]]) == int:
                inputs[inputs_keys[selected]] += 1
        elif key == "KEY_DOWN":
            if type(inputs[inputs_keys[selected]]) == int:
                inputs[inputs_keys[selected]] -= 1
        elif key == "\n":
            if type(inputs[inputs_keys[selected]]) != int:
                return inputs[inputs_keys[selected]]