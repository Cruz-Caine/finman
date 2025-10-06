import curses # imports curses a barebones highly portable tui library
from finman.ui.main_menu import MainMenu
import argparse

def main():
    screen = curses.initscr() # creates the screen object we will be working with
    curses_init(screen)
    
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
        curses.napms(100)
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
