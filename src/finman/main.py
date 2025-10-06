import curses # imports curses a barebones highly portable tui library
from finman.ui.main_menu import MainMenu
import argparse

def main():
    screen = curses.initscr() # creates the screen object we will be working with
    curses_init()
    
    inpt = screen.getch()
    main_menu = MainMenu(screen)
    current_scene = main_menu
    while inpt != curses.KEY_ENTER and inpt != 10 and inpt!= 13:

        scene = None
        current_scene.full_pass(inpt,scene)

        if scene != None:
            current_scene = scene
        # limit the speed of the app
        curses.napms(100)
        # check for key presses
        inpt = screen.getch()

    curses_exit()
    

def curses_init():
    curses.noecho() # stops key presses from being shown on the screen by default
    curses.cbreak() # get key presses without the user pressing enter
    screen.keypad(True) # get special values instead of multi-key sequences for certain key presses
    screen.nodelay(True) # make getchr non-blocking
    curses.curs_set(0) # disable the cursor
    curses.start_color() # enable the usage of colors

def curses_exit():
    # Undoes all the changes we made to the terminal during initialization
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    main()
