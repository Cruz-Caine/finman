import curses # imports curses, a barebones highly portable tui library
from curses import textpad
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from enum import Enum

class DIALOG_TYPE(Enum):
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4


class Dialog(Scene):
    def __init__(self, screen, pred_scene, message="", options=None, portion=2):
        super().__init__(screen, pred_scene)
        self.portion = portion
        self.message = message
        self.options = options if options else []
        self.selected = 0
        self.result = None
        num_rows, num_cols = self.screen.getmaxyx()
        dialog_height = num_rows // portion
        dialog_width = num_cols // portion
        start_y = (num_rows - dialog_height) // 2
        start_x = (num_cols - dialog_width) // 2
        self.dialog_window = curses.newwin(dialog_height, dialog_width, start_y, start_x)

    def handle_input(self, input):
        if input == curses.KEY_ENTER or input == 10 or input == 13:
            # Store the selected option and return to previous scene
            if self.options:
                self.result = self.options[self.selected]
            self.change_scene = self.pred_scene
        elif input == 9:  # Tab key
            # Cycle through options
            if self.options:
                self.selected = (self.selected + 1) % len(self.options)
        elif input == ord('a'):
            self.change_scene = self.pred_scene
        elif input == 27:  # Escape key
            self.change_scene = self.pred_scene

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        num_rows, num_cols = self.screen.getmaxyx()
        dialog_height = num_rows // self.portion
        dialog_width = num_cols // self.portion
        start_y = (num_rows - dialog_height) // 2
        start_x = (num_cols - dialog_width) // 2

        # Resize and reposition the dialog window
        self.dialog_window.resize(dialog_height, dialog_width)
        self.dialog_window.mvwin(start_y, start_x)

        # Add a border to the dialog window
        self.dialog_window.box()

        # Display the message
        if self.message:
            self.dialog_window.addstr(1, 2, self.message[:dialog_width - 4])

        # Build menu with options if provided
        if self.options:
            build_menu(self.dialog_window, self.options, self.selected, row_off=3, col_off=2)

        # Display help text at bottom
        help_text = "Tab: Navigate | Enter: Select | Esc: Cancel"
        if dialog_height > 5:  # Only show if there's room
            self.dialog_window.addstr(dialog_height - 2, 2, help_text[:dialog_width - 4])

        return None

    def render(self):
        self.dialog_window.refresh()
        self.screen.refresh()
        self.screen.clear()

    def on_enter(self):
        pass

    def on_exit(self):
        super().on_exit()

    def get_result(self):
        """Returns the selected option, or None if dialog was cancelled"""
        return self.result




