import curses # imports curses a barebones highly portable tui library
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from finman.ui.transactions import Transactions
from finman.ui.budget import Budget


class MainMenu(Scene):
    def __init__(self,screen,pred_screen):
        super().__init__(screen,None)
        self.entered = False
        self.selected = 0
        self.options = ["Overview", "Transations", "Budget"]
        self.menu_window = curses.newwin(1, 1, 3, 0)
        self.title_window = curses.newwin(1, 1, 0, 0)
        self.help_window = curses.newwin(1, 1, 0, 0)
        self.name = "Finman"
        self.tagline = "The Financial Management App"
        self.fullname = self.name + ": " + self.tagline
        pass

    def handle_input(self, input):
        if input == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                # Check if click is in menu window
                win_y, win_x = self.menu_window.getbegyx()
                win_h, win_w = self.menu_window.getmaxyx()

                if win_y <= my < win_y + win_h and win_x <= mx < win_x + win_w:
                    # Calculate which option was clicked based on vertical centering
                    # Options are evenly spaced vertically
                    rel_y = my - win_y
                    spacing = win_h // len(self.options)
                    clicked_option = rel_y // spacing

                    if 0 <= clicked_option < len(self.options):
                        self.selected = clicked_option
                        # On click, trigger selection
                        if bstate & curses.BUTTON1_CLICKED:
                            if self.selected == 1:
                                self.change_scene = Transactions(self.screen,self)
                            elif self.selected == 2:
                                self.change_scene = Budget(self.screen,self)
            except:
                pass
        elif input == curses.KEY_ENTER or input == 10 or input == 13:
            if self.selected == 1:
                self.change_scene = Transactions(self.screen,self)
            elif self.selected == 2:
                self.change_scene = Budget(self.screen,self)
        elif input == 27:
            exit()
        elif input == curses.KEY_DOWN:
            self.selected = (self.selected+1)%len(self.options)
        elif input == curses.KEY_UP:
            self.selected = (self.selected-1)%len(self.options)

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        num_rows, num_cols = self.screen.getmaxyx()
        # resize the title_window to take up 3 rows two for the border and one for the title itself
        self.title_window.resize(3,num_cols)
        # add a border to the title_window
        self.title_window.box()
        # center the title in the title window
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        self.title_window.addstr(1,(num_cols-len(self.fullname))//2,self.fullname,curses.color_pair(1))

        # Help window at bottom
        help_text = "↑/↓: Navigate | Enter: Select | Esc: Quit"
        self.help_window.resize(1, num_cols)
        self.help_window.mvwin(num_rows - 1, 0)
        self.help_window.clear()
        self.help_window.addstr(0, 2, help_text[:num_cols - 4])

        # border the menu window
        self.menu_window.box()
        # resize it if needed (leave space for help bar)
        self.menu_window.resize(num_rows-4, num_cols)
        # convience function to make menu
        build_menu(self.menu_window,self.options,self.selected,row_cen=1,col_cen=1)
        return None

    def render(self):
        self.screen.clear()
        self.screen.refresh()
        self.menu_window.refresh()
        self.title_window.refresh()
        self.help_window.refresh()
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        super().on_exit()
        pass

