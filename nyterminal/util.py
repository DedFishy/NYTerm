import curses
import requests
from nyterminal.const import COLORS

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

def get_starting_dimensions_yx(width, height, max_yx):
    y_coord, x_coord = max_yx
    y_coord /= 2
    x_coord /= 2
    y_coord -= height/2
    x_coord -= width/2

    y_coord = int(y_coord)
    x_coord = int(x_coord)
    return y_coord, x_coord

def render_rows_to_center(rows: list[tuple[str,int]|dict[str,int]], stdscr: curses.window, center_all = True):
    width = max((len("".join(list(row.keys()))) if type(row) == dict else len(row[0]) for row in rows))
    y_coord, x_coord = get_starting_dimensions_yx(width, len(rows), stdscr.getmaxyx())

    row_dimensions = {}

    for row in rows:
        if type(row) == list:
            current_x = x_coord
            row_width = len("".join(x[0] for x in row))
            current_x += int(width/2 - row_width/2)
            for section in row:
                addstr(stdscr, y_coord, current_x, section[0], curses.color_pair(section[1]))
                current_x += len(section[0])
        else:
            addstr(stdscr, y_coord, x_coord, row[0].center(width) if center_all else row[0], curses.color_pair(row[1]))
            if len(row) > 2:
                row_dimensions[row[2]] = y_coord
        y_coord += 1
    return row_dimensions

def run_row_selector(inputs: dict[str, int|bool], stdscr: curses.window, default, title):
    
    inputs_keys = list(inputs.keys())
    selected = default
    still_selecting = True
    while still_selecting:
        stdscr.clear()
        option_positions = {}
        row = []
        row.append((" | ", 0))
        for input in inputs_keys:
            option_positions[input] = len("".join(x[0] for x in row))
            row.append((f"{input}" + (f": {inputs[input]}" if type(inputs[input]) == int else ""), COLORS["SELECTED_OPTION" if input == inputs_keys[selected] else "UNSELECTED_OPTION"]))
            row.append((" | ", 0))
        render_rows_to_center([
            (title,COLORS["SUBTITLE"]), 
            row
        ],
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
        elif key == "KEY_MOUSE":
            mouse = curses.getmouse()
            x_offset = mouse[1] - (int(stdscr.getmaxyx()[1]/2 - len("".join(x[0] for x in row))/2))

            if mouse[4] == 2:

                clicked = None
                for option in option_positions.keys():
                    if option_positions[option] < x_offset:
                        clicked = option
                    else:
                        break
                if clicked:
                    _log(mouse, x_offset, clicked, option_positions)
                    old_selected = selected
                    selected = list(inputs.keys()).index(clicked)
                    if selected == old_selected and type(inputs[inputs_keys[selected]]) == bool:
                        return inputs, inputs[inputs_keys[selected]]
            

        elif key == "\n":
            if type(inputs[inputs_keys[selected]]) != int:
                return inputs, inputs[inputs_keys[selected]]

def get_average(list):
    if len(list) == 0: return 0
    return sum(list)/len(list)

def run_button_row(inputs: list[str], stdscr: curses.window, default, title):
    
    selected = default
    still_selecting = True
    while still_selecting:
        stdscr.clear()
        option_positions = {}
        row = []
        row.append((" | ", 0))
        for input in inputs:
            option_positions[input] = len("".join(x[0] for x in row))
            row.append((f"{input}", COLORS["SELECTED_OPTION" if inputs.index(input) == selected else "UNSELECTED_OPTION"]))
            row.append((" | ", 0))
        render_rows_to_center([
            (title,COLORS["SUBTITLE"]), 
            row
        ],
        stdscr)
        
        key = stdscr.getkey()
        if key == "KEY_LEFT" and selected > 0:
            selected -= 1
        elif key == "KEY_RIGHT" and selected < len(inputs) - 1: 
            selected += 1
        elif key == "KEY_MOUSE":
            mouse = curses.getmouse()
            x_offset = mouse[1] - (int(stdscr.getmaxyx()[1]/2 - len("".join(x[0] for x in row))/2))

            if mouse[4] == 2:

                clicked = None
                for option in option_positions.keys():
                    if option_positions[option] < x_offset:
                        clicked = option
                    else:
                        break
                if clicked:
                    _log(mouse, x_offset, clicked, option_positions)
                    old_selected = selected
                    selected = inputs.index(clicked)
                    if selected == old_selected:
                        return clicked
            

        elif key == "\n":
            return inputs[selected]
            
def prompt_screen_resize(stdscr: curses.window):
    stdscr.clear()
    render_rows_to_center([("Your terminal is too small!", 0), ("Resize it or lower your text size", 0), ("([CTRL+C] to quit)", 0)], stdscr)
    stdscr.refresh()

def show_dialog(stdscr: curses.window, text):
    stdscr.clear()
    render_rows_to_center([(text, 0), ("OKAY", COLORS["SELECTED_OPTION"])], stdscr)
    stdscr.refresh()
    stdscr.getkey()

def addstr(stdscr: curses.window, y_coord=0, x_coord=0, text="", attr=0):
    try:
        stdscr.addstr(y_coord, x_coord, text, attr)
    except curses.error:
        prompt_screen_resize(stdscr)
            
def _log(*string):
    conv_string = []
    for element in string:
        conv_string.append(str(element))
    with open("log.txt", "w+") as file:
        file.write("|".join(conv_string))