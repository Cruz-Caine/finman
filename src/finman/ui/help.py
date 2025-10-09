import curses
from finman.ui.scene import Scene


class Help(Scene):
    def __init__(self, screen, pred_scene):
        super().__init__(screen, pred_scene)
        self.help_content_pad = curses.newpad(1000, 500)
        self.help_border = curses.newwin(1, 1, 3, 0)
        self.title_window = curses.newwin(1, 1, 0, 0)
        self.help_bar_window = curses.newwin(1, 1, 0, 0)
        self.scroll_offset = 0

        # Help content
        self.help_lines = [
            "FINMAN - FINANCIAL MANAGEMENT APPLICATION",
            "",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            "OVERVIEW:",
            "  View budget usage for a specific period with visual progress bars.",
            "  - Color coding: Green (<50%), Yellow (50-80%), Red (80%+)",
            "  - Shows spending vs budget for all tags and subtags",
            "  - Navigate between periods with ←/→ arrows",
            "",
            "  Controls:",
            "    ↑/↓        - Navigate through items",
            "    ←/→        - Change period (month/year)",
            "    Tab        - Cycle through sort options",
            "    Type       - Search/filter by name or tag ID",
            "    Esc        - Return to main menu",
            "",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            "TRANSACTIONS:",
            "  Manage all your financial transactions.",
            "",
            "  Controls:",
            "    ↑/↓        - Navigate through transactions",
            "    a          - Add new transaction",
            "    Enter      - Edit selected transaction",
            "    Ctrl+D     - Delete selected transaction",
            "    Tab        - Cycle through sort options (Date/Amount/Tag)",
            "    Type       - Search by description, amount, or tag",
            "    #tag       - Filter by specific tag (e.g., #food or #food/dining)",
            "    Esc        - Return to main menu",
            "",
            "  Transaction Editor:",
            "    Tab/Shift+Tab  - Navigate between fields",
            "    ↑/↓            - Select tag/subtag from dropdown",
            "    Enter          - Save transaction",
            "    Esc            - Cancel",
            "",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            "BUDGET:",
            "  Set and manage budget limits for different spending categories.",
            "  Budget is organized by tags (categories) and subtags (subcategories).",
            "",
            "  Controls:",
            "    ↑/↓        - Navigate through budget items",
            "    ←/→        - Change period (month/year)",
            "    a          - Add new tag or subtag",
            "    Enter      - Edit selected tag/subtag",
            "    Ctrl+D     - Delete selected tag/subtag",
            "    Tab        - Cycle through sort options",
            "    Type       - Search/filter by name or ID",
            "    Esc        - Return to main menu",
            "",
            "  Budget Editor:",
            "    Tab/Shift+Tab  - Navigate between fields",
            "    ↑/↓            - Select parent tag (for subtags)",
            "    Enter          - Save budget item",
            "    Esc            - Cancel",
            "",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            "TIPS:",
            "  • Tags represent broad spending categories (e.g., Food, Transport)",
            "  • Subtags represent specific subcategories (e.g., Dining Out, Groceries)",
            "  • Use #tag syntax in Transactions search to filter by category",
            "  • Progress bars in Overview show how much of your budget you've used",
            "  • Click with mouse to select items and navigate (double-click to edit)",
            "  • All changes are automatically saved to budget_data.json",
            "",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            "Press Esc to return to the main menu",
        ]

    def handle_input(self, input):
        # Mouse handling
        if input == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                # Allow scrolling with mouse wheel or clicking
                if bstate & curses.BUTTON4_PRESSED:  # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 3)
                elif bstate & curses.BUTTON5_PRESSED:  # Scroll down
                    self.scroll_offset += 3
            except:
                pass
        # Escape key
        elif input == 27:
            self.change_scene = self.pred_scene
        # Navigation controls
        elif input == curses.KEY_UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif input == curses.KEY_DOWN:
            self.scroll_offset += 1
        elif input == curses.KEY_PPAGE:  # Page Up
            self.scroll_offset = max(0, self.scroll_offset - 10)
        elif input == curses.KEY_NPAGE:  # Page Down
            self.scroll_offset += 10

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        num_rows, num_cols = self.screen.getmaxyx()

        # Title window at top
        self.title_window.resize(3, num_cols)
        self.title_window.mvwin(0, 0)
        self.title_window.clear()
        self.title_window.box()
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        title = "Help & Instructions"
        self.title_window.addstr(1, (num_cols - len(title)) // 2, title, curses.color_pair(1))

        # Help bar at bottom
        help_text = "↑/↓/PgUp/PgDn: Scroll | Esc: Back to Menu"
        self.help_bar_window.resize(1, num_cols)
        self.help_bar_window.mvwin(num_rows - 1, 0)
        self.help_bar_window.clear()
        self.help_bar_window.addstr(0, 2, help_text[:num_cols - 4])

        # Help content border
        self.help_border.resize(num_rows - 4, num_cols)
        self.help_border.mvwin(3, 0)
        self.help_border.clear()
        self.help_border.box()

        # Populate help content pad
        self.help_content_pad.clear()
        for idx, line in enumerate(self.help_lines):
            try:
                # Add some color to section headers
                if line and (line.startswith("FINMAN") or "═══" in line):
                    self.help_content_pad.addstr(idx, 2, line, curses.color_pair(1))
                elif line.endswith(":") and not line.startswith(" "):
                    self.help_content_pad.addstr(idx, 2, line, curses.color_pair(1) | curses.A_BOLD)
                else:
                    self.help_content_pad.addstr(idx, 2, line)
            except:
                pass

        # Limit scroll offset
        viewport_height = num_rows - 4 - 2
        max_scroll = max(0, len(self.help_lines) - viewport_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        return None

    def render(self):
        self.screen.clear()
        self.screen.refresh()
        self.title_window.refresh()
        self.help_border.refresh()
        self.help_bar_window.refresh()

        # Refresh pad to show visible portion
        num_rows, num_cols = self.screen.getmaxyx()

        # Calculate viewport coordinates
        pad_top = self.scroll_offset
        pad_left = 0
        screen_top = 3 + 1  # Below title + border
        screen_left = 0 + 1  # Border
        screen_bottom = num_rows - 1 - 1 - 1  # Bottom - help bar - border
        screen_right = num_cols - 1 - 1  # Right - border

        self.help_content_pad.refresh(
            pad_top, pad_left,
            screen_top, screen_left,
            screen_bottom, screen_right
        )

    def on_enter(self):
        self.needs_render = True

    def on_exit(self):
        super().on_exit()
