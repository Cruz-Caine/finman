import curses
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from finman.util.dialog import Dialog
from finman.ui.budget_editor import BudgetEditor
from finman.logic.financial_data import FinancialData


class Budget(Scene):
    def __init__(self, screen, pred_scene):
        super().__init__(screen, pred_scene)
        self.search_window = curses.newwin(3, 1, 0, 0)
        self.search_text = ""
        self.sort_window = curses.newwin(1, 1, 3, 0)
        self.sort_selected = 0
        self.budget_pad = curses.newpad(10000, 500)
        self.budget_border = curses.newwin(1, 1, 3, 21)
        self.budget_selected = 0
        self.scroll_offset = 0
        self.sort_options = ["Date-Ascending", "Date-Descending", "Name-Ascending", "Name-Descending", "Amount-Ascending", "Amount-Descending"]
        self.findata = FinancialData()
        self.budget_items = []  # Flattened list of budget items
        self.pending_delete = None
        self.pending_add = False
        self.last_dialog = None

    def _get_sorted_budget_items(self):
        """Get budget items (tags and subtags) sorted based on current sort selection."""
        items = []

        # Flatten budget structure into displayable items
        for budget in self.findata.get_all_budgets():
            year = budget["year"]
            month = budget["month"]

            for tag in budget.get("tags", []):
                # Add tag as an item
                items.append({
                    "type": "tag",
                    "year": year,
                    "month": month,
                    "id": tag["id"],
                    "name": tag["name"],
                    "maxAmount": tag["maxAmount"],
                    "parent_id": None
                })

                # Add subtags
                for subtag in tag.get("subTags", []):
                    items.append({
                        "type": "subtag",
                        "year": year,
                        "month": month,
                        "id": subtag["id"],
                        "name": subtag["name"],
                        "maxAmount": subtag["maxAmount"],
                        "parent_id": tag["id"]
                    })

        # Sort based on selection
        if self.sort_selected == 0:  # Date-Ascending
            items = sorted(items, key=lambda i: (i["year"], i["month"]))
        elif self.sort_selected == 1:  # Date-Descending
            items = sorted(items, key=lambda i: (i["year"], i["month"]), reverse=True)
        elif self.sort_selected == 2:  # Name-Ascending
            items = sorted(items, key=lambda i: i["name"].lower())
        elif self.sort_selected == 3:  # Name-Descending
            items = sorted(items, key=lambda i: i["name"].lower(), reverse=True)
        elif self.sort_selected == 4:  # Amount-Ascending
            items = sorted(items, key=lambda i: i["maxAmount"])
        elif self.sort_selected == 5:  # Amount-Descending
            items = sorted(items, key=lambda i: i["maxAmount"], reverse=True)

        return items

    def _filter_by_search(self, items):
        """Filter budget items based on search text."""
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

            # Check date
            date = f"{item['year']}-{item['month']:02d}"
            if search_lower in date:
                filtered.append(item)
                continue

            # Check amount
            amount = f"{item['maxAmount']:.2f}"
            if search_lower in amount:
                filtered.append(item)
                continue

        return filtered

    def _format_budget_item(self, item):
        """Format a budget item for display."""
        date = f"{item['year']}-{item['month']:02d}"
        amount = f"${item['maxAmount']:>8.2f}"

        # Indent subtags
        if item["type"] == "subtag":
            prefix = "  └─ "
        else:
            prefix = ""

        name = f"{prefix}{item['name']}"
        item_id = f"[{item['id']}]"

        return f"{date} | {item_id:<15} | {name:<25} | {amount}"

    def handle_input(self, input):
        # Tab: cycle forward through sort options
        if input == 9:  # Tab
            self.sort_selected = (self.sort_selected + 1) % len(self.sort_options)
        # Shift+Tab: cycle backward through sort options
        elif input == 353:  # Shift+Tab
            self.sort_selected = (self.sort_selected - 1) % len(self.sort_options)
        # 'a' key: Add new tag or subtag
        elif input == ord('a'):
            # Show dialog to choose between tag and subtag
            dialog = Dialog(
                self.screen, self,
                message="Add Tag or Subtag?",
                options=["Tag", "Subtag", "Cancel"],
                portion=4
            )
            self.last_dialog = dialog
            self.change_scene = dialog
            self.pending_add = True
        # Enter key: Edit selected item
        elif input == curses.KEY_ENTER or input == 10 or input == 13:
            if self.budget_items and self.budget_selected < len(self.budget_items):
                selected_item = self.budget_items[self.budget_selected]
                item_type = selected_item["type"]
                self.change_scene = BudgetEditor(
                    self.screen, self,
                    mode="edit",
                    item_type=item_type,
                    item=selected_item
                )
        # Ctrl+D: Delete selected item
        elif input == 4:  # Ctrl+D
            if self.budget_items and self.budget_selected < len(self.budget_items):
                selected_item = self.budget_items[self.budget_selected]
                item_type = "tag" if selected_item["type"] == "tag" else "subtag"
                dialog = Dialog(
                    self.screen, self,
                    message=f"Delete {item_type}: {selected_item['name']}?",
                    options=["Yes", "No"],
                    portion=4
                )
                self.last_dialog = dialog
                self.change_scene = dialog
                self.pending_delete = selected_item
        # Escape key
        elif input == 27:
            self.change_scene = self.pred_scene
        # Backspace: remove last character from search
        elif input in (curses.KEY_BACKSPACE, 127, 8):
            if self.search_text:
                self.search_text = self.search_text[:-1]
        # Navigation controls
        elif input == curses.KEY_UP:
            self.budget_selected = max(0, self.budget_selected - 1)
        elif input == curses.KEY_DOWN:
            self.budget_selected += 1
        # Printable characters: add to search text
        elif 32 <= input <= 126:
            self.search_text += chr(input)

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        # Get sorted and filtered budget items
        sorted_items = self._get_sorted_budget_items()
        self.budget_items = self._filter_by_search(sorted_items)
        formatted_items = [self._format_budget_item(i) for i in self.budget_items]

        # Keep budget_selected within bounds
        if formatted_items:
            self.budget_selected = max(0, min(self.budget_selected, len(formatted_items) - 1))
        else:
            self.budget_selected = 0

        num_rows, num_cols = self.screen.getmaxyx()

        # Search bar at top: 3 rows, full width
        self.search_window.resize(3, num_cols)
        self.search_window.mvwin(0, 0)
        self.search_window.clear()
        self.search_window.box()

        # Display search text and sort mode in search bar
        sort_mode = self.sort_options[self.sort_selected]
        search_display = f"Search: {self.search_text}" if self.search_text else "Search: (type to filter)"
        status = f"Sort: {sort_mode}"

        self.search_window.addstr(1, 2, search_display[:num_cols - 4])
        if len(status) < num_cols - 4:
            self.search_window.addstr(1, num_cols - len(status) - 2, status)

        # Sort window below search bar: left side, 20 columns
        self.sort_window.resize(num_rows - 3, 20)
        self.sort_window.mvwin(3, 0)
        self.sort_window.clear()
        self.sort_window.box()

        # Budget border window below search bar: right side, remaining width
        self.budget_border.resize(num_rows - 3, num_cols - 20)
        self.budget_border.mvwin(3, 20)
        self.budget_border.clear()
        self.budget_border.box()

        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        build_menu(self.sort_window, self.sort_options, self.sort_selected, row_off=1, col_off=1)

        # Display budget items using pad
        if formatted_items:
            # Clear pad and draw all budget items
            self.budget_pad.clear()
            build_menu(self.budget_pad, formatted_items, self.budget_selected, row_off=0, col_off=0)

            # Calculate viewport dimensions (inside border)
            viewport_height = num_rows - 3 - 2  # Screen height - top bar - borders
            viewport_width = num_cols - 20 - 2   # Screen width - left panel - borders

            # Adjust scroll offset to keep selected item visible
            if self.budget_selected < self.scroll_offset:
                self.scroll_offset = self.budget_selected
            elif self.budget_selected >= self.scroll_offset + viewport_height:
                self.scroll_offset = self.budget_selected - viewport_height + 1

            # Ensure scroll offset is within bounds
            max_scroll = max(0, len(formatted_items) - viewport_height)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        return None

    def render(self):
        self.search_window.refresh()
        self.sort_window.refresh()
        self.budget_border.refresh()

        # Refresh pad to show visible portion
        num_rows, num_cols = self.screen.getmaxyx()
        if self.budget_items:
            # Calculate viewport coordinates (inside border)
            pad_top = self.scroll_offset
            pad_left = 0
            screen_top = 3 + 1  # Below search bar + border
            screen_left = 20 + 1  # After sort window + border
            screen_bottom = num_rows - 1 - 1  # Bottom of screen - border
            screen_right = num_cols - 1 - 1  # Right of screen - border

            self.budget_pad.refresh(
                pad_top, pad_left,
                screen_top, screen_left,
                screen_bottom, screen_right
            )

        self.screen.refresh()
        self.screen.clear()

    def on_enter(self):
        # Check if we're returning from an add dialog
        if self.pending_add and self.last_dialog:
            result = self.last_dialog.get_result()
            if result == "Tag":
                self.change_scene = BudgetEditor(self.screen, self, mode="add", item_type="tag")
            elif result == "Subtag":
                self.change_scene = BudgetEditor(self.screen, self, mode="add", item_type="subtag")
            # Clear pending add and dialog reference
            self.pending_add = False
            self.last_dialog = None

        # Check if we're returning from a delete confirmation dialog
        elif self.pending_delete and self.last_dialog:
            result = self.last_dialog.get_result()
            if result == "Yes":
                # Delete the tag or subtag
                item = self.pending_delete
                if item["type"] == "tag":
                    self.findata.remove_tag(item["year"], item["month"], item["id"])
                else:  # subtag
                    self.findata.remove_subtag(item["year"], item["month"], item["parent_id"], item["id"])
            # Clear pending delete and dialog reference
            self.pending_delete = None
            self.last_dialog = None

    def on_exit(self):
        super().on_exit()
