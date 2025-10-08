import curses # imports curses, a barebones highly portable tui library
from curses import textpad
from finman.util.menus import build_menu
from finman.ui.scene import Scene
from finman.util.dialog import Dialog
from finman.ui.transaction_editor import TransactionEditor
from finman.logic.financial_data import FinancialData



class Transactions(Scene):
    def __init__(self,screen,pred_scene):
        super().__init__(screen,pred_scene)
        self.search_window = curses.newwin(3, 1, 0, 0)
        self.search_text = ""
        self.search_active = True
        self.sort_window = curses.newwin(1, 1, 3, 0)
        self.sort_selected = 0
        self.transactions_pad = curses.newpad(10000, 500)
        self.transactions_border = curses.newwin(1, 1, 3, 21)
        self.transactions_selected = 0
        self.scroll_offset = 0
        self.help_window = curses.newwin(1, 1, 0, 0)
        self.left_options = ["Date-Ascending","Date-Descending","Quan-Ascending","Quan-Descending"]
        self.findata = FinancialData()
        self.sorted_transactions = []
        self.pending_delete = None
        self.last_dialog = None
        pass

    def _get_sorted_transactions(self):
        """Get transactions sorted based on current sort selection."""
        transactions = self.findata.get_all_transactions()

        if self.sort_selected == 0:  # Date-Ascending
            return sorted(transactions, key=lambda t: (t['year'], t['month'], t['day']))
        elif self.sort_selected == 1:  # Date-Descending
            return sorted(transactions, key=lambda t: (t['year'], t['month'], t['day']), reverse=True)
        elif self.sort_selected == 2:  # Quan-Ascending
            return sorted(transactions, key=lambda t: t['amount'])
        elif self.sort_selected == 3:  # Quan-Descending
            return sorted(transactions, key=lambda t: t['amount'], reverse=True)

        return transactions

    def _format_transaction(self, transaction):
        """Format a transaction for display."""
        date = f"{transaction['year']}-{transaction['month']:02d}-{transaction['day']:02d}"
        amount = f"${transaction['amount']:.2f}"
        description = transaction['description']
        tag = transaction.get('tagId', '')
        subtag = transaction.get('subtagId', '')

        # Format tags
        if subtag:
            tags = f"#{tag}/{subtag}"
        else:
            tags = f"#{tag}"

        return f"{date} | {amount:>10} | {description} {tags}"

    def _filter_by_search(self, transactions):
        """Filter transactions based on search text."""
        if not self.search_text:
            return transactions

        search_lower = self.search_text.lower()
        filtered = []

        # Check if searching by tag (#tag or #tag/subtag)
        if search_lower.startswith('#'):
            tag_search = search_lower[1:]  # Remove the #

            for transaction in transactions:
                tag = transaction.get('tagId', '').lower()
                subtag = transaction.get('subtagId', '').lower() if transaction.get('subtagId') else ''

                # Check if matches tag or tag/subtag format
                if '/' in tag_search:
                    # Searching for specific tag/subtag
                    if tag_search == f"{tag}/{subtag}":
                        filtered.append(transaction)
                else:
                    # Searching for just tag
                    if tag_search in tag or tag_search in subtag:
                        filtered.append(transaction)
            return filtered

        # Regular search (non-tag)
        for transaction in transactions:
            # Check if search text appears in description
            if search_lower in transaction['description'].lower():
                filtered.append(transaction)
                continue

            # Check if search text appears in date
            date = f"{transaction['year']}-{transaction['month']:02d}-{transaction['day']:02d}"
            if search_lower in date:
                filtered.append(transaction)
                continue

            # Check if search text appears in amount
            amount = f"{transaction['amount']:.2f}"
            if search_lower in amount:
                filtered.append(transaction)
                continue

        return filtered

    def handle_input(self,input):
        # Mouse handling
        if input == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()

                # Check click in sort window (left panel)
                sort_y, sort_x = self.sort_window.getbegyx()
                sort_h, sort_w = self.sort_window.getmaxyx()
                if sort_y <= my < sort_y + sort_h and sort_x <= mx < sort_x + sort_w:
                    # Clicked in sort window - calculate which option
                    rel_y = my - sort_y - 1  # -1 for border
                    if 0 <= rel_y < len(self.left_options):
                        self.sort_selected = rel_y

                # Check click in transactions area (right panel)
                trans_y, trans_x = self.transactions_border.getbegyx()
                trans_h, trans_w = self.transactions_border.getmaxyx()
                if trans_y <= my < trans_y + trans_h and trans_x <= mx < trans_x + trans_w:
                    # Clicked in transactions area
                    rel_y = my - trans_y - 1  # -1 for border
                    # Calculate which transaction (accounting for scroll offset)
                    clicked_index = rel_y + self.scroll_offset
                    if 0 <= clicked_index < len(self.sorted_transactions):
                        self.transactions_selected = clicked_index
                        # Double-click to edit
                        if bstate & curses.BUTTON1_DOUBLE_CLICKED:
                            selected_transaction = self.sorted_transactions[self.transactions_selected]
                            self.change_scene = TransactionEditor(self.screen, self, mode="edit", transaction=selected_transaction)
            except:
                pass
        # Tab: cycle forward through sort options
        elif input == 9:  # Tab
            self.sort_selected = (self.sort_selected + 1) % len(self.left_options)
        # Shift+Tab: cycle backward through sort options
        elif input == 353:  # Shift+Tab (curses.KEY_BTAB)
            self.sort_selected = (self.sort_selected - 1) % len(self.left_options)
        # 'a' key: Add new transaction
        elif input == ord('a'):
            self.change_scene = TransactionEditor(self.screen, self, mode="add")
        # Enter key: Edit selected transaction
        elif input == curses.KEY_ENTER or input == 10 or input == 13:
            if self.sorted_transactions and self.transactions_selected < len(self.sorted_transactions):
                selected_transaction = self.sorted_transactions[self.transactions_selected]
                self.change_scene = TransactionEditor(self.screen, self, mode="edit", transaction=selected_transaction)
        # Ctrl+D: Delete selected transaction
        elif input == 4:  # Ctrl+D
            if self.sorted_transactions and self.transactions_selected < len(self.sorted_transactions):
                selected_transaction = self.sorted_transactions[self.transactions_selected]
                # Show confirmation dialog
                dialog = Dialog(
                    self.screen, self,
                    message=f"Delete transaction: {selected_transaction['description']}?",
                    options=["Yes", "No"],
                    portion=4
                )
                self.last_dialog = dialog
                self.change_scene = dialog
                # Store transaction to delete for later
                self.pending_delete = selected_transaction
        # Escape key
        elif input == 27:
            self.change_scene = self.pred_scene
        # Backspace: remove last character from search
        elif input in (curses.KEY_BACKSPACE, 127, 8):
            if self.search_text:
                self.search_text = self.search_text[:-1]
        # Navigation controls for transactions
        elif input == curses.KEY_UP:
            self.transactions_selected = max(0, self.transactions_selected - 1)
        elif input == curses.KEY_DOWN:
            # Bounds checking happens in update()
            self.transactions_selected += 1
        # Printable characters: add to search text
        elif 32 <= input <= 126:  # Printable ASCII characters
            self.search_text += chr(input)

    def update(self):
        if self.change_scene:
            scene = self.change_scene
            return scene

        # Get sorted and filtered transactions
        sorted_trans = self._get_sorted_transactions()
        self.sorted_transactions = self._filter_by_search(sorted_trans)
        formatted_transactions = [self._format_transaction(t) for t in self.sorted_transactions]

        # Keep transactions_selected within bounds
        if formatted_transactions:
            self.transactions_selected = max(0, min(self.transactions_selected, len(formatted_transactions) - 1))
        else:
            self.transactions_selected = 0

        num_rows, num_cols = self.screen.getmaxyx()

        # Search bar at top: 3 rows, full width
        self.search_window.resize(3, num_cols)
        self.search_window.mvwin(0, 0)
        self.search_window.clear()
        self.search_window.box()

        # Display search text and sort mode in search bar
        sort_mode = self.left_options[self.sort_selected]
        search_display = f"Search: {self.search_text}" if self.search_text else "Search: (type to filter)"
        status = f"Sort: {sort_mode}"

        self.search_window.addstr(1, 2, search_display[:num_cols - 4])
        if len(status) < num_cols - 4:
            self.search_window.addstr(1, num_cols - len(status) - 2, status)

        # Help window at bottom
        help_text = "a: Add | Enter: Edit | Ctrl+D: Delete | Tab: Sort | Type: Search | #tag: Filter | Esc: Back"
        self.help_window.resize(1, num_cols)
        self.help_window.mvwin(num_rows - 1, 0)
        self.help_window.clear()
        self.help_window.addstr(0, 2, help_text[:num_cols - 4])

        # Sort window below search bar: left side, 20 columns (leave space for help bar)
        self.sort_window.resize(num_rows - 4, 20)
        self.sort_window.mvwin(3, 0)
        self.sort_window.clear()
        self.sort_window.box()

        # Transactions border window below search bar: right side, remaining width (leave space for help bar)
        self.transactions_border.resize(num_rows - 4, num_cols - 20)
        self.transactions_border.mvwin(3, 20)
        self.transactions_border.clear()
        self.transactions_border.box()

        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        build_menu(self.sort_window, self.left_options, self.sort_selected, row_off=1, col_off=1)

        # Display transactions using pad
        if formatted_transactions:
            # Clear pad and draw all transactions
            self.transactions_pad.clear()
            build_menu(self.transactions_pad, formatted_transactions, self.transactions_selected, row_off=0, col_off=0)

            # Calculate viewport dimensions (inside border)
            viewport_height = num_rows - 4 - 2  # Screen height - top bar - help bar - borders
            viewport_width = num_cols - 20 - 2   # Screen width - left panel - borders

            # Adjust scroll offset to keep selected item visible
            if self.transactions_selected < self.scroll_offset:
                self.scroll_offset = self.transactions_selected
            elif self.transactions_selected >= self.scroll_offset + viewport_height:
                self.scroll_offset = self.transactions_selected - viewport_height + 1

            # Ensure scroll offset is within bounds
            max_scroll = max(0, len(formatted_transactions) - viewport_height)
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        pass
        return None

    def render(self):
        self.screen.clear()
        self.screen.refresh()
        self.search_window.refresh()
        self.sort_window.refresh()
        self.transactions_border.refresh()
        self.help_window.refresh()

        # Refresh pad to show visible portion
        num_rows, num_cols = self.screen.getmaxyx()
        if self.sorted_transactions:
            # Calculate viewport coordinates (inside border)
            pad_top = self.scroll_offset
            pad_left = 0
            screen_top = 3 + 1  # Below search bar + border
            screen_left = 20 + 1  # After sort window + border
            screen_bottom = num_rows - 1 - 1 - 1  # Bottom of screen - help bar - border
            screen_right = num_cols - 1 - 1  # Right of screen - border

            self.transactions_pad.refresh(
                pad_top, pad_left,
                screen_top, screen_left,
                screen_bottom, screen_right
            )

        pass

    def on_enter(self):
        # Check if we're returning from a delete confirmation dialog
        if self.pending_delete and self.last_dialog:
            result = self.last_dialog.get_result()
            if result == "Yes":
                # Delete the transaction
                self.findata.remove_transaction(self.pending_delete["id"])
            # Clear pending delete and dialog reference
            self.pending_delete = None
            self.last_dialog = None
        pass

    def on_exit(self):
        super().on_exit()
        pass



