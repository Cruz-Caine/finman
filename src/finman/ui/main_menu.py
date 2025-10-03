import curses # imports curses a barebones highly portable tui library
from finman.util.menus import build_menu

def main():
    name = "Finman"
    tagline = "The Financial Management App"
    fullmane = name + ": " + tagline
    screen = curses.initscr() # creates the screen object we will be working with
    curses.noecho() # stops key presses from being shown on the screen by default
    curses.cbreak() # get key presses without the user pressing enter
    screen.keypad(True) # get special values instead of multi-key sequences for certain key presses
    screen.nodelay(True) # make getchr non-blocking
    curses.curs_set(0) # disable the cursor
    curses.start_color() # enable the usage of colors
    num_rows, num_cols = screen.getmaxyx() 
    menu_window = curses.newwin(1, 1, 3, 0)
    title_window = curses.newwin(1, 1, 0, 0)
    
    options = ["Overview", "Add Transations", "Modify Budget"]
    inpt = screen.getch()
    selected = 0
    while inpt != curses.KEY_ENTER and inpt != 10 and inpt!= 13:
        if inpt == curses.KEY_DOWN:
            selected = (selected+1)%len(options)
        elif inpt == curses.KEY_UP:
            selected = (selected-1)%len(options)
        num_rows, num_cols = screen.getmaxyx() 

        # resize the title_window to take up 3 rows two for the border and one for the title itself
        title_window.resize(3,num_cols)
        # add a border to the title_window
        title_window.box()
        # center the title in the title window
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        title_window.addstr(1,(num_cols-len(fullmane))//2,fullmane,curses.color_pair(1))

        
        # border the menu window
        menu_window.box()
        # resize it if needed
        menu_window.resize(num_rows-3,num_cols)
        # convience function to make menu
        build_menu(menu_window,options,selected,row_cen=1,col_cen=1)

        
        # update both windows
        menu_window.refresh()
        title_window.refresh()
        screen.refresh()
        screen.clear()
        

        # limit the speed of the app
        curses.napms(100)
        # check for key presses
        inpt = screen.getch()
    
    # Undoes all the changes we made to the terminal during initialization
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    main()
