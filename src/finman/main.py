import curses # imports curses a barebones highly portable tui library
from finman.ui.main_menu import MainMenu
import argparse

def main():
    screen = curses.initscr() # creates the screen object we will be working with
    curses_init(screen)
    #args = parser.parse_args()
    #parser.add_argument('filename', help='Input file to process')
    #args = parser.parse_args()
    #try:
    #    with open(args.filename, 'r') as f:
    #        data = json.load(f)
    #    
    #    # Do something with the data
    #    if args.pretty:
    #        print(json.dumps(data, indent=2))
    #    else:
    #        print(data)
    
    input = None
    main_menu = MainMenu(screen,None)
    current_scene = main_menu
    while True:

        scene = current_scene.full_pass(input)

        if scene != None:
            current_scene.on_exit()
            current_scene = scene
            current_scene.on_enter()
        # limit the speed of the app
        curses.napms(25)
        # check for key presses
        input = screen.getch()

    curses_exit()
    

def curses_init(screen):
    curses.noecho() # stops key presses from being shown on the screen by default
    curses.cbreak() # get key presses without the user pressing enter
    screen.keypad(True) # get special values instead of multi-key sequences for certain key presses
    screen.nodelay(True) # make getchr non-blocking
    curses.curs_set(0) # disable the cursor
    curses.start_color() # enable the usage of colors

def curses_exit(screen):
    # Undoes all the changes we made to the terminal during initialization
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    main()
