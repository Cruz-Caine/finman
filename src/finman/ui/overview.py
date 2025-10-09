import curses
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from finman.logic.financial_data import FinancialData


class Overview(Scene):
    def __init__(self, screen, pred_scene):
        super().__init__(screen, pred_scene)
        self.search_window = curses.newwin(3, 1, 0, 0)
        self.search_text = ""
        self.sort_window = curses.newwin(1, 1, 3, 0)
        self.sort_selected = 0
        self.overview_pad = curses.newpad(10000, 500)
        self.overview_border = curses.newwin(1, 1, 3, 21)
        self.overview_selected = 0
        self.scroll_offset = 0
        self.help_window = curses.newwin(1, 1, 0, 0)
        self.sort_options = ["Name-Ascending", "Name-Descending", "Usage-Ascending", "Usage-Descending"]
        self.findata = FinancialData()
        self.overview_items = []  # Flattened list of budget items with usage data

        # Current period viewing
        self.available_periods = self._get_available_periods()
        self.current_period_index = 0 if self.available_periods else -1

    def _get_available_periods(self):
        """Get list of available budget periods sorted by date."""
        periods = []
        for budget in self.findata.get_all_budgets():
            periods.append((budget["year"], budget["month"]))
        return sorted(periods)

    def _get_current_period(self):
        """Get the currently selected period."""
        if self.current_period_index >= 0 and self.current_period_index < len(self.available_periods):
            return self.available_periods[self.current_period_index]
        return None

    def _calculate_tag_spending(self, year, month, tag_id, subtag_id=None):
        """Calculate total spending for a tag or subtag in a given period."""
        transactions = self.findata.get_transactions_by_date(year, month)
        total = 0.0

        for transaction in transactions:
            if transaction["tagId"] == tag_id:
                if subtag_id is None:
                    # For parent tags, only count transactions without subtags
                    if not transaction.get("subtagId"):
                        total += transaction["amount"]
                else:
                    # For subtags, match both tag and subtag
                    if transaction.get("subtagId") == subtag_id:
                        total += transaction["amount"]

        return total

    def _get_sorted_overview_items(self):
        """Get overview items (tags and subtags) with usage data."""
        # Get current period
        current_period = self._get_current_period()
        if not current_period:
            return []

        year, month = current_period

        # Get budget for current period
        budget = self.findata.get_budget(year, month)
        if not budget:
            return []

        # Build overview items with spending data
        tag_groups = []
        for tag in budget.get("tags", []):
            tag_spending = self._calculate_tag_spending(year, month, tag["id"])
            tag_item = {
                "type": "tag",
                "year": year,
                "month": month,
                "id": tag["id"],
                "name": tag["name"],
                "maxAmount": tag["maxAmount"],
                "spent": tag_spending,
                "percentage": (tag_spending / tag["maxAmount"] * 100) if tag["maxAmount"] > 0 else 0,
                "parent_id": None
            }

            subtag_items = []
            for subtag in tag.get("subTags", []):
                subtag_spending = self._calculate_tag_spending(year, month, tag["id"], subtag["id"])
                subtag_items.append({
                    "type": "subtag",
                    "year": year,
                    "month": month,
                    "id": subtag["id"],
                    "name": subtag["name"],
                    "maxAmount": subtag["maxAmount"],
                    "spent": subtag_spending,
                    "percentage": (subtag_spending / subtag["maxAmount"] * 100) if subtag["maxAmount"] > 0 else 0,
                    "parent_id": tag["id"]
                })

            tag_groups.append((tag_item, subtag_items))

        # Sort tag groups based on selection
        if self.sort_selected == 0:  # Name-Ascending
            tag_groups = sorted(tag_groups, key=lambda g: g[0]["name"].lower())
        elif self.sort_selected == 1:  # Name-Descending
            tag_groups = sorted(tag_groups, key=lambda g: g[0]["name"].lower(), reverse=True)
        elif self.sort_selected == 2:  # Usage-Ascending
            tag_groups = sorted(tag_groups, key=lambda g: g[0]["percentage"])
        elif self.sort_selected == 3:  # Usage-Descending
            tag_groups = sorted(tag_groups, key=lambda g: g[0]["percentage"], reverse=True)

        # Flatten back to list
        items = []
        for tag_item, subtag_items in tag_groups:
            items.append(tag_item)
            items.extend(subtag_items)

        return items

    def _filter_by_search(self, items):
        """Filter overview items based on search text."""
        if not self.search_text:
            return items

        search_lower = self.search_text.lower()
        filtered = []

        for item in items:
            # Check name
            if search_lower in item["name"].lower():
                filtered.append(item)
                continue

            # Check id
            if search_lower in item["id"].lower():
                filtered.append(item)
                continue

        return filtered

    def _get_progress_bar(self, percentage, width=10):
        """Generate a progress bar string like [######   ]"""
        filled = int((percentage / 100.0) * width)
        filled = max(0, min(filled, width))  # Clamp to 0-width
        empty = width - filled
        return f"[{'#' * filled}{' ' * empty}]"

    def _get_color_for_percentage(self, percentage):
        """Get color pair based on percentage used."""
        if percentage < 50:
            return 3  # Green
        elif percentage < 80:
            return 4  # Yellow
        else:
            return 2  # Red

    def _format_overview_item(self, item, is_selected):
        """Format an overview item for display with progress bar and color."""
        # Indent subtags
        if item["type"] == "subtag":
            prefix = "  └─ "
        else:
            prefix = ""

        name = f"{prefix}{item['name']}"
        item_id = f"[{item['id']}]"
        spent = f"${item['spent']:>8.2f}"
        budget = f"${item['maxAmount']:>8.2f}"
        progress_bar = self._get_progress_bar(item["percentage"], width=12)
        percentage_str = f"{item['percentage']:>5.1f}%"

        # Get color attribute
        color_pair = self._get_color_for_percentage(item["percentage"])

        return (f"{item_id:<15} | {name:<25} | {spent} / {budget} {progress_bar} {percentage_str}", color_pair)

    def handle_input(self, input):
        # Mouse handling
        if input == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()

                # Check click in sort window (left panel)
                sort_y, sort_x = self.sort_window.getbegyx()
                sort_h, sort_w = self.sort_window.getmaxyx()
                if sort_y <= my < sort_y + sort_h and sort_x <= mx < sort_x + sort_w:
                    # Clicked in sort window
                    rel_y = my - sort_y - 1
                    if 0 <= rel_y < len(self.sort_options):
                        self.sort_selected = rel_y

                # Check click in overview area (right panel)
                overview_y, overview_x = self.overview_border.getbegyx()
                overview_h, overview_w = self.overview_border.getmaxyx()
                if overview_y <= my < overview_y + overview_h and overview_x <= mx < overview_x + overview_w:
                    # Clicked in overview area
                    rel_y = my - overview_y - 1
                    clicked_index = rel_y + self.scroll_offset
                    if 0 <= clicked_index < len(self.overview_items):
                        self.overview_selected = clicked_index

                # Check click in search bar for period navigation
                search_y, search_x = self.search_window.getbegyx()
                search_h, search_w = self.search_window.getmaxyx()
                if search_y <= my < search_y + search_h and search_x <= mx < search_x + search_w:
                    num_rows, num_cols = self.screen.getmaxyx()
                    if mx > search_x + search_w - 30:
                        if mx < search_x + search_w - 15:
                            # Previous period
                            if self.available_periods:
                                self.current_period_index = (self.current_period_index - 1) % len(self.available_periods)
                                self.overview_selected = 0
                                self.scroll_offset = 0
                        else:
                            # Next period
                            if self.available_periods:
                                self.current_period_index = (self.current_period_index + 1) % len(self.available_periods)
                                self.overview_selected = 0
                                self.scroll_offset = 0
            except:
                pass
        # Left arrow: previous period
        elif input == curses.KEY_LEFT:
            if self.available_periods:
                self.current_period_index = (self.current_period_index - 1) % len(self.available_periods)
                self.overview_selected = 0
                self.scroll_offset = 0
        # Right arrow: next period
        elif input == curses.KEY_RIGHT:
            if self.available_periods:
                self.current_period_index = (self.current_period_index + 1) % len(self.available_periods)
                self.overview_selected = 0
                self.scroll_offset = 0
        # Tab: cycle forward through sort options
        elif input == 9:  # Tab
            self.sort_selected = (self.sort_selected + 1) % len(self.sort_options)
        # Shift+Tab: cycle backward through sort options
        elif input == 353:  # Shift+Tab
            self.sort_selected = (self.sort_selected - 1) % len(self.sort_options)
        # Escape key
        elif input == 27:
            self.change_scene = self.pred_scene
        # Backspace: remove last character from search
        elif input in (curses.KEY_BACKSPACE, 127, 8):
            if self.search_text:
                self.search_text = self.search_text[:-1]
        # Navigation controls
        elif input == curses.KEY_UP:
            self.overview_selected = max(0, self.overview_selected - 1)
        elif input == curses.KEY_DOWN:
            self.overview_selected += 1
        # Printable characters: add to search text
        elif 32 <= input <= 126:
            self.search_text += chr(input)

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        # Get sorted and filtered overview items
        sorted_items = self._get_sorted_overview_items()
        self.overview_items = self._filter_by_search(sorted_items)

        # Keep overview_selected within bounds
        if self.overview_items:
            self.overview_selected = max(0, min(self.overview_selected, len(self.overview_items) - 1))
        else:
            self.overview_selected = 0

        num_rows, num_cols = self.screen.getmaxyx()

        # Search bar at top: 3 rows, full width
        self.search_window.resize(3, num_cols)
        self.search_window.mvwin(0, 0)
        self.search_window.clear()
        self.search_window.box()

        # Display period, search text and sort mode in search bar
        current_period = self._get_current_period()
        if current_period:
            year, month = current_period
            period_display = f"{year}-{month:02d}"
        else:
            period_display = "No budgets"

        sort_mode = self.sort_options[self.sort_selected]
        search_display = f"Search: {self.search_text}" if self.search_text else "Search: (type to filter)"
        status = f"Period: {period_display} | Sort: {sort_mode} | ←/→ to change period"

        self.search_window.addstr(1, 2, search_display[:num_cols - 4])
        if len(status) < num_cols - 4:
            self.search_window.addstr(1, num_cols - len(status) - 2, status)

        # Help window at bottom
        help_text = "↑/↓: Navigate | ←/→: Period | Tab: Sort | Type: Search | Esc: Back"
        self.help_window.resize(1, num_cols)
        self.help_window.mvwin(num_rows - 1, 0)
        self.help_window.clear()
        self.help_window.addstr(0, 2, help_text[:num_cols - 4])

        # Sort window below search bar: left side, 20 columns
        self.sort_window.resize(num_rows - 4, 20)
        self.sort_window.mvwin(3, 0)
        self.sort_window.clear()
        self.sort_window.box()

        # Overview border window below search bar: right side, remaining width
        self.overview_border.resize(num_rows - 4, num_cols - 20)
        self.overview_border.mvwin(3, 20)
        self.overview_border.clear()
        self.overview_border.box()

        # Initialize color pairs
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Selection highlight
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # High usage (80%+)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Low usage (<50%)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Medium usage (50-80%)

        build_menu(self.sort_window, self.sort_options, self.sort_selected, row_off=1, col_off=1)

        # Display overview items using pad with colors
        if self.overview_items:
            # Clear pad
            self.overview_pad.clear()

            # Draw all overview items with colors
            for idx, item in enumerate(self.overview_items):
                text, color_pair = self._format_overview_item(item, idx == self.overview_selected)

                # Apply color and highlight if selected
                if idx == self.overview_selected:
                    attr = curses.color_pair(1) | curses.A_REVERSE
                else:
                    attr = curses.color_pair(color_pair)

                try:
                    self.overview_pad.addstr(idx, 0, text, attr)
                except:
                    pass

            # Calculate viewport dimensions
            viewport_height = num_rows - 4 - 2
            viewport_width = num_cols - 20 - 2

            # Adjust scroll offset to keep selected item visible
            if self.overview_selected < self.scroll_offset:
                self.scroll_offset = self.overview_selected
            elif self.overview_selected >= self.scroll_offset + viewport_height:
                self.scroll_offset = self.overview_selected - viewport_height + 1

            # Ensure scroll offset is within bounds
            max_scroll = max(0, len(self.overview_items) - viewport_height)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        return None

    def render(self):
        self.screen.clear()
        self.screen.refresh()
        self.search_window.refresh()
        self.sort_window.refresh()
        self.overview_border.refresh()
        self.help_window.refresh()

        # Refresh pad to show visible portion
        num_rows, num_cols = self.screen.getmaxyx()
        if self.overview_items:
            # Calculate viewport coordinates
            pad_top = self.scroll_offset
            pad_left = 0
            screen_top = 3 + 1
            screen_left = 20 + 1
            screen_bottom = num_rows - 1 - 1 - 1
            screen_right = num_cols - 1 - 1

            self.overview_pad.refresh(
                pad_top, pad_left,
                screen_top, screen_left,
                screen_bottom, screen_right
            )

    def on_enter(self):
        # Refresh available periods in case new budgets were added
        old_periods = self.available_periods
        self.available_periods = self._get_available_periods()

        # If periods changed, adjust current index
        if old_periods != self.available_periods:
            if not self.available_periods:
                self.current_period_index = -1
            elif self.current_period_index >= len(self.available_periods):
                self.current_period_index = len(self.available_periods) - 1
            elif self.current_period_index < 0:
                self.current_period_index = 0

        self.needs_render = True

    def on_exit(self):
        super().on_exit()
