# NYTerminal
## Play the (good) NYT games within your terminal!
If you ever find yourself in a situation where you have borked your Linux system and are left with nothing but a terminal, or you are being paid by the hour to use a server interface, or you are bored and don't have a browser handy, kill some time with the New York Times games in your terminal!

This program takes advantage of the fact that the free NYT games are publicly available on their servers. For the Wordle, Connections, and the Strands, there are named files for each date (including future dates!) that contain the JSON data for each day. The Mini is similar, but it only has today's puzzle. The Spelling Bee has its data embedded in the webpage, so an HTML parser has been used to facilitate it.

### Installation
Simply install the package with `pip`: `python3 -m pip install nyterminal`

### Running
Run the package (NAMED DIFFERENTLY) with `python3 -m nyterminal` or `nyterminal` if your default Python environment is the one NYTerminal is installed to.

### Interface
Using Curses, the terminal window is turned into a highly interactive UI. Most elements can be clicked, or you can use your arrow keys to navigate menus. While the controls are intuitive, here's a handy reference:
| Key                      | Function                     |
| ------------------------ | ---------------------------- |
| Up/Down/Left/Right Arrow | Navigate Menu/Increment Date |
| Enter                    | Activate Button/Submit Guess |
| Space                    | Select (Strands, Connections)|
| Tab                      | Use Hint (Strands)           |
| Escape                   | Exit Game (Saving)           |
| Control + C              | Quit Program                 |
NOTE: If you use CTRL+C to close the program with a game open, that game's data will not be recorded to your stats!