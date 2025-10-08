import curses
from finman.ui.scene import Scene
from finman.logic.financial_data import FinancialData
from datetime import datetime


class TransactionEditor(Scene):
    def __init__(self, screen, pred_scene, mode="add", transaction=None):
        """
        Initialize transaction editor popup.

        Args:
            mode: "add" or "edit"
            transaction: Transaction dict if editing, None if adding
        """
        super().__init__(screen, pred_scene)
        self.mode = mode
        self.findata = FinancialData()

        # Field names and current field index
        self.field_names = ["year", "month", "day", "amount", "description", "tag", "subtag"]
        self.current_field = 0

        # Initialize field values
        if mode == "edit" and transaction:
            self.fields = {
                "year": str(transaction.get("year", "")),
                "month": str(transaction.get("month", "")),
                "day": str(transaction.get("day", "")),
                "amount": str(transaction.get("amount", "")),
                "description": transaction.get("description", ""),
                "tag": transaction.get("tagId", ""),
                "subtag": transaction.get("subtagId", "")
            }
            self.transaction_id = transaction.get("id", "")
        else:
            # Default to today's date for new transactions
            today = datetime.now()
            self.fields = {
                "year": str(today.year),
                "month": str(today.month),
                "day": str(today.day),
                "amount": "",
                "description": "",
                "tag": "",
                "subtag": ""
            }
            self.transaction_id = self._generate_transaction_id()

        # Get available tags from budgets
        self.available_tags = self._get_available_tags()
        self.tag_selected_index = 0
        self.subtag_selected_index = 0

        # Create centered popup window
        num_rows, num_cols = self.screen.getmaxyx()
        self.popup_height = min(20, num_rows - 4)
        self.popup_width = min(60, num_cols - 4)
        start_y = (num_rows - self.popup_height) // 2
        start_x = (num_cols - self.popup_width) // 2
        self.popup_window = curses.newwin(self.popup_height, self.popup_width, start_y, start_x)

    def _generate_transaction_id(self):
        """Generate a unique transaction ID."""
        existing_ids = [t["id"] for t in self.findata.get_all_transactions()]
        counter = 1
        while True:
            new_id = f"txn_{counter:03d}"
            if new_id not in existing_ids:
                return new_id
            counter += 1

    def _get_available_tags(self):
        """Get list of available tags from all budgets."""
        tags = {}
        for budget in self.findata.get_all_budgets():
            for tag in budget.get("tags", []):
                tag_id = tag["id"]
                if tag_id not in tags:
                    tags[tag_id] = {
                        "name": tag["name"],
                        "subtags": []
                    }
                # Collect all possible subtags
                for subtag in tag.get("subTags", []):
                    subtag_id = subtag["id"]
                    if subtag_id not in [st["id"] for st in tags[tag_id]["subtags"]]:
                        tags[tag_id]["subtags"].append({
                            "id": subtag_id,
                            "name": subtag["name"]
                        })
        return tags

    def _get_tag_list(self):
        """Get list of tag IDs."""
        return list(self.available_tags.keys())

    def _get_subtag_list(self):
        """Get list of subtag IDs for currently selected tag."""
        current_tag = self.fields.get("tag", "")
        if current_tag and current_tag in self.available_tags:
            return [st["id"] for st in self.available_tags[current_tag]["subtags"]]
        return []

    def handle_input(self, input):
        field_name = self.field_names[self.current_field]

        # Mouse handling
        if input == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                # Check if click is in popup window
                win_y, win_x = self.popup_window.getbegyx()
                win_h, win_w = self.popup_window.getmaxyx()

                if win_y <= my < win_y + win_h and win_x <= mx < win_x + win_w:
                    # Calculate which field was clicked (fields start at row 3)
                    rel_y = my - win_y - 3
                    # Map row to field index, accounting for skipped fields
                    field_row = 0
                    for i, fname in enumerate(self.field_names):
                        if fname == "subtag" and not self._get_subtag_list():
                            continue
                        if field_row == rel_y:
                            self.current_field = i
                            break
                        field_row += 1
            except:
                pass
        # Tab: move to next field
        elif input == 9:  # Tab
            self.current_field = (self.current_field + 1) % len(self.field_names)
            # Skip subtag field if current tag has no subtags
            if self.field_names[self.current_field] == "subtag" and not self._get_subtag_list():
                self.current_field = (self.current_field + 1) % len(self.field_names)

        # Shift+Tab: move to previous field
        elif input == 353:  # Shift+Tab
            self.current_field = (self.current_field - 1) % len(self.field_names)
            # Skip subtag field if current tag has no subtags
            if self.field_names[self.current_field] == "subtag" and not self._get_subtag_list():
                self.current_field = (self.current_field - 1) % len(self.field_names)

        # Enter: save transaction
        elif input == curses.KEY_ENTER or input == 10 or input == 13:
            self._save_transaction()

        # Escape: cancel
        elif input == 27:
            self.change_scene = self.pred_scene

        # For tag and subtag fields: use up/down to cycle options
        elif field_name == "tag":
            if input == curses.KEY_UP:
                tag_list = self._get_tag_list()
                if tag_list:
                    current_tag = self.fields.get("tag", "")
                    if current_tag in tag_list:
                        idx = tag_list.index(current_tag)
                        idx = (idx - 1) % len(tag_list)
                    else:
                        idx = 0
                    self.fields["tag"] = tag_list[idx]
                    self.fields["subtag"] = ""  # Reset subtag when tag changes
            elif input == curses.KEY_DOWN:
                tag_list = self._get_tag_list()
                if tag_list:
                    current_tag = self.fields.get("tag", "")
                    if current_tag in tag_list:
                        idx = tag_list.index(current_tag)
                        idx = (idx + 1) % len(tag_list)
                    else:
                        idx = 0
                    self.fields["tag"] = tag_list[idx]
                    self.fields["subtag"] = ""  # Reset subtag when tag changes

        elif field_name == "subtag":
            if input == curses.KEY_UP:
                subtag_list = self._get_subtag_list()
                if subtag_list:
                    current_subtag = self.fields.get("subtag", "")
                    if current_subtag in subtag_list:
                        idx = subtag_list.index(current_subtag)
                        idx = (idx - 1) % len(subtag_list)
                    else:
                        idx = 0
                    self.fields["subtag"] = subtag_list[idx]
            elif input == curses.KEY_DOWN:
                subtag_list = self._get_subtag_list()
                if subtag_list:
                    current_subtag = self.fields.get("subtag", "")
                    if current_subtag in subtag_list:
                        idx = subtag_list.index(current_subtag)
                        idx = (idx + 1) % len(subtag_list)
                    else:
                        idx = 0
                    self.fields["subtag"] = subtag_list[idx]

        # For text input fields: handle characters and backspace
        elif field_name in ["year", "month", "day", "amount", "description"]:
            if input in (curses.KEY_BACKSPACE, 127, 8):
                if self.fields[field_name]:
                    self.fields[field_name] = self.fields[field_name][:-1]
            elif 32 <= input <= 126:  # Printable characters
                self.fields[field_name] += chr(input)

    def _save_transaction(self):
        """Validate and save the transaction."""
        try:
            # Validate fields
            year = int(self.fields["year"])
            month = int(self.fields["month"])
            day = int(self.fields["day"])
            amount = float(self.fields["amount"])
            description = self.fields["description"]
            tag_id = self.fields["tag"]
            subtag_id = self.fields.get("subtag", "") or None

            if not description:
                raise ValueError("Description is required")
            if not tag_id:
                raise ValueError("Tag is required")
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
            if day < 1 or day > 31:
                raise ValueError("Day must be between 1 and 31")

            # Save transaction
            if self.mode == "add":
                self.findata.add_transaction(
                    self.transaction_id, year, month, day,
                    amount, description, tag_id, subtag_id
                )
            else:  # edit mode
                self.findata.edit_transaction(
                    self.transaction_id,
                    year=year, month=month, day=day,
                    amount=amount, description=description,
                    tag_id=tag_id, subtag_id=subtag_id
                )

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
        popup_height = min(20, num_rows - 4)
        popup_width = min(60, num_cols - 4)
        start_y = (num_rows - popup_height) // 2
        start_x = (num_cols - popup_width) // 2

        # Resize and reposition popup
        self.popup_window.resize(popup_height, popup_width)
        self.popup_window.mvwin(start_y, start_x)
        self.popup_window.clear()
        self.popup_window.box()

        # Title
        title = "Add Transaction" if self.mode == "add" else "Edit Transaction"
        self.popup_window.addstr(1, 2, title, curses.A_BOLD)

        # Display fields
        row = 3
        for i, field_name in enumerate(self.field_names):
            # Skip subtag if no subtags available
            if field_name == "subtag" and not self._get_subtag_list():
                continue

            # Field label
            label = field_name.capitalize() + ":"

            # Get field value display
            if field_name == "tag":
                tag_id = self.fields.get("tag", "")
                if tag_id and tag_id in self.available_tags:
                    value = f"{tag_id} ({self.available_tags[tag_id]['name']})"
                else:
                    value = "(select with up/down)" if not tag_id else tag_id
            elif field_name == "subtag":
                subtag_id = self.fields.get("subtag", "")
                current_tag = self.fields.get("tag", "")
                if subtag_id and current_tag in self.available_tags:
                    subtags = self.available_tags[current_tag]["subtags"]
                    subtag_obj = next((st for st in subtags if st["id"] == subtag_id), None)
                    if subtag_obj:
                        value = f"{subtag_id} ({subtag_obj['name']})"
                    else:
                        value = subtag_id
                else:
                    value = "(optional, use up/down)"
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
        self.screen.clear()
        self.screen.refresh()
        self.popup_window.refresh()

    def on_enter(self):
        pass

    def on_exit(self):
        super().on_exit()
