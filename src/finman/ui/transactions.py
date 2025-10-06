import curses # imports curses a barebones highly portable tui library
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from finman.util.menus import build_menu
from finman.ui.scene import Scene


class Transactions(Scene):
    def __init__(self,screen,pred_scene):
        super().__init__(screen,pred_scene)
        self.sort_window = curses.newwin(1, 1, 0, 0)
        self.sort_selected = 0
        self.left_options = ["Date-Ascending","Date-Descending","Quan-Ascending","Quan-Descending"]
        pass

    def handle_input(self,input):
        if input == curses.KEY_ENTER or input == 10 or input == 13:
            pass
        if input ==  27:
            self.change_scene = self.pred_scene
            pass

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        num_rows, num_cols = self.screen.getmaxyx() 
        # resize the title_window to take up 3 rows two for the border and one for the title itself
        self.sort_window.resize(num_rows,20)
        # add a border to the title_window
        self.sort_window.box()
        # center the title in the title window
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        build_menu(self.sort_window,self.left_options,self.sort_selected,row_off=1,col_off=1)
        pass
        return None

    def render(self):
        self.sort_window.refresh()
        self.screen.refresh()
        self.screen.clear()
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        super().on_exit()
        pass



