import curses # imports curses a barebones highly portable tui library
from finman.util.menus import build_menu
from finman.ui.scene import Scene

def main():
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
    
    # Undoes all the changes we made to the terminal during initialization
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()


class MainMenu(Scene):
    def __init__(self,screen):
        super().__init__(screen)
        self.entered = False
        self.selected = 0
        self.options = ["Overview", "Add Transations", "Modify Budget"]
        self.menu_window = curses.newwin(1, 1, 3, 0)
        self.title_window = curses.newwin(1, 1, 0, 0)
        self.screen = screen
        self.name = "Finman"
        self.tagline = "The Financial Management App"
        self.fullname = self.name + ": " + self.tagline
        pass

    def handle_input(self, input):
        if input == curses.KEY_DOWN:
            self.selected = (self.selected+1)%len(self.options)
        elif input == curses.KEY_UP:
            self.selected = (self.selected-1)%len(self.options)

    def update(self,scene):
        num_rows, num_cols = self.screen.getmaxyx() 
        # resize the title_window to take up 3 rows two for the border and one for the title itself
        self.title_window.resize(3,num_cols)
        # add a border to the title_window
        self.title_window.box()
        # center the title in the title window
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        self.title_window.addstr(1,(num_cols-len(self.fullname))//2,self.fullname,curses.color_pair(1))


        # border the menu window
        self.menu_window.box()
        # resize it if needed
        self.menu_window.resize(num_rows-3,num_cols)
        # convience function to make menu
        build_menu(self.menu_window,self.options,self.selected,row_cen=1,col_cen=1)
        pass

    def render(self):
        self.menu_window.refresh()
        self.title_window.refresh()
        self.screen.refresh()
        self.screen.clear()
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        pass

if __name__ == "__main__":
    main()
