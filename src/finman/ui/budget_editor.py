import curses
from finman.ui.scene import Scene
from finman.logic.financial_data import FinancialData
from datetime import datetime


class BudgetEditor(Scene):
    def __init__(self, screen, pred_scene, mode="add", item_type="tag", item=None):
        """
        Initialize budget editor popup.

        Args:
            mode: "add" or "edit"
            item_type: "tag" or "subtag"
            item: Budget item dict if editing, None if adding
        """
        super().__init__(screen, pred_scene)
        self.mode = mode
        self.item_type = item_type
        self.findata = FinancialData()

        # Field names based on item type
        if item_type == "tag":
            self.field_names = ["year", "month", "tag_id", "name", "max_amount"]
        else:  # subtag
            self.field_names = ["year", "month", "parent_tag", "subtag_id", "name", "max_amount"]

        self.current_field = 0

        # Initialize field values
        if mode == "edit" and item:
            if item_type == "tag":
                self.fields = {
                    "year": str(item.get("year", "")),
                    "month": str(item.get("month", "")),
                    "tag_id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "max_amount": str(item.get("maxAmount", ""))
                }
            else:  # subtag
                self.fields = {
                    "year": str(item.get("year", "")),
                    "month": str(item.get("month", "")),
                    "parent_tag": item.get("parent_id", ""),
                    "subtag_id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "max_amount": str(item.get("maxAmount", ""))
                }
            self.original_item = item
        else:
            # Default to current month for new items
            today = datetime.now()
            if item_type == "tag":
                self.fields = {
                    "year": str(today.year),
                    "month": str(today.month),
                    "tag_id": "",
                    "name": "",
                    "max_amount": ""
                }
            else:  # subtag
                self.fields = {
                    "year": str(today.year),
                    "month": str(today.month),
                    "parent_tag": "",
                    "subtag_id": "",
                    "name": "",
                    "max_amount": ""
                }
            self.original_item = None

        # Get available parent tags for subtag mode
        self.available_parent_tags = self._get_available_parent_tags()

        # Create centered popup window
        num_rows, num_cols = self.screen.getmaxyx()
        self.popup_height = min(18, num_rows - 4)
        self.popup_width = min(60, num_cols - 4)
        start_y = (num_rows - self.popup_height) // 2
        start_x = (num_cols - self.popup_width) // 2
        self.popup_window = curses.newwin(self.popup_height, self.popup_width, start_y, start_x)

    def _get_available_parent_tags(self):
        """Get list of available parent tags from all budgets."""
        tags = {}
        for budget in self.findata.get_all_budgets():
            for tag in budget.get("tags", []):
                tag_id = tag["id"]
                if tag_id not in tags:
                    tags[tag_id] = tag["name"]
        return tags

    def _get_parent_tag_list(self):
        """Get list of parent tag IDs."""
        return list(self.available_parent_tags.keys())

    def handle_input(self, input):
        field_name = self.field_names[self.current_field]

        # Tab: move to next field
        if input == 9:  # Tab
            self.current_field = (self.current_field + 1) % len(self.field_names)

        # Shift+Tab: move to previous field
        elif input == 353:  # Shift+Tab
            self.current_field = (self.current_field - 1) % len(self.field_names)

        # Enter: save item
        elif input == curses.KEY_ENTER or input == 10 or input == 13:
            self._save_item()

        # Escape: cancel
        elif input == 27:
            self.change_scene = self.pred_scene

        # For parent_tag field: use up/down to cycle options
        elif field_name == "parent_tag":
            if input == curses.KEY_UP:
                tag_list = self._get_parent_tag_list()
                if tag_list:
                    current_tag = self.fields.get("parent_tag", "")
                    if current_tag in tag_list:
                        idx = tag_list.index(current_tag)
                        idx = (idx - 1) % len(tag_list)
                    else:
                        idx = 0
                    self.fields["parent_tag"] = tag_list[idx]
            elif input == curses.KEY_DOWN:
                tag_list = self._get_parent_tag_list()
                if tag_list:
                    current_tag = self.fields.get("parent_tag", "")
                    if current_tag in tag_list:
                        idx = tag_list.index(current_tag)
                        idx = (idx + 1) % len(tag_list)
                    else:
                        idx = 0
                    self.fields["parent_tag"] = tag_list[idx]

        # For text input fields: handle characters and backspace
        else:
            if input in (curses.KEY_BACKSPACE, 127, 8):
                if self.fields[field_name]:
                    self.fields[field_name] = self.fields[field_name][:-1]
            elif 32 <= input <= 126:  # Printable characters
                self.fields[field_name] += chr(input)

    def _save_item(self):
        """Validate and save the tag or subtag."""
        try:
            # Validate common fields
            year = int(self.fields["year"])
            month = int(self.fields["month"])
            name = self.fields["name"]
            max_amount = float(self.fields["max_amount"])

            if not name:
                raise ValueError("Name is required")
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")

            # Save based on item type
            if self.item_type == "tag":
                tag_id = self.fields["tag_id"]
                if not tag_id:
                    raise ValueError("Tag ID is required")

                # Check if budget exists, create if not
                budget = self.findata.get_budget(year, month)
                if not budget and self.mode == "add":
                    self.findata.add_budget(year, month)

                if self.mode == "add":
                    self.findata.add_tag(year, month, tag_id, name, max_amount)
                else:  # edit mode
                    self.findata.edit_tag(year, month, tag_id, name=name, max_amount=max_amount)

            else:  # subtag
                parent_tag = self.fields["parent_tag"]
                subtag_id = self.fields["subtag_id"]

                if not parent_tag:
                    raise ValueError("Parent tag is required")
                if not subtag_id:
                    raise ValueError("Subtag ID is required")

                # Check if budget exists, create if not
                budget = self.findata.get_budget(year, month)
                if not budget and self.mode == "add":
                    self.findata.add_budget(year, month)

                if self.mode == "add":
                    self.findata.add_subtag(year, month, parent_tag, subtag_id, name, max_amount)
                else:  # edit mode
                    self.findata.edit_subtag(year, month, parent_tag, subtag_id, name=name, max_amount=max_amount)

            # Return to previous scene
            self.change_scene = self.pred_scene

        except ValueError as e:
            # TODO: Show error message to user
            # For now, just don't save
            pass

    def update(self):
        if self.change_scene:
            return self.change_scene

        num_rows, num_cols = self.screen.getmaxyx()
        popup_height = min(18, num_rows - 4)
        popup_width = min(60, num_cols - 4)
        start_y = (num_rows - popup_height) // 2
        start_x = (num_cols - popup_width) // 2

        # Resize and reposition popup
        self.popup_window.resize(popup_height, popup_width)
        self.popup_window.mvwin(start_y, start_x)
        self.popup_window.clear()
        self.popup_window.box()

        # Title
        action = "Add" if self.mode == "add" else "Edit"
        item_type_display = "Tag" if self.item_type == "tag" else "Subtag"
        title = f"{action} {item_type_display}"
        self.popup_window.addstr(1, 2, title, curses.A_BOLD)

        # Display fields
        row = 3
        for i, field_name in enumerate(self.field_names):
            # Field label
            label_map = {
                "year": "Year:",
                "month": "Month:",
                "tag_id": "Tag ID:",
                "subtag_id": "Subtag ID:",
                "parent_tag": "Parent Tag:",
                "name": "Name:",
                "max_amount": "Max Amount:"
            }
            label = label_map.get(field_name, field_name.capitalize() + ":")

            # Get field value display
            if field_name == "parent_tag":
                tag_id = self.fields.get("parent_tag", "")
                if tag_id and tag_id in self.available_parent_tags:
                    value = f"{tag_id} ({self.available_parent_tags[tag_id]})"
                else:
                    value = "(select with up/down)" if not tag_id else tag_id
            else:
                value = self.fields.get(field_name, "")

            # Highlight current field
            if i == self.current_field:
                self.popup_window.addstr(row, 2, label, curses.A_BOLD)
                self.popup_window.addstr(row, 18, value[:popup_width - 22], curses.A_STANDOUT)
            else:
                self.popup_window.addstr(row, 2, label)
                self.popup_window.addstr(row, 18, value[:popup_width - 22])

            row += 1

        # Instructions
        instructions = "Tab/Shift+Tab: Navigate | Enter: Save | Esc: Cancel"
        if row < popup_height - 2:
            self.popup_window.addstr(popup_height - 2, 2, instructions[:popup_width - 4])

        return None

    def render(self):
        self.popup_window.refresh()
        self.screen.refresh()
        self.screen.clear()

    def on_enter(self):
        pass

    def on_exit(self):
        super().on_exit()
