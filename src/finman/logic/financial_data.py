import json
import os
from typing import Optional, Dict, List, Any


class FinancialData:
    """Singleton class for managing budget and transaction data from JSON file."""

    _instance: Optional['FinancialData'] = None
    _initialized: bool = False

    def __new__(cls, file_path: str = "budget_data.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, file_path: str = "budget_data.json"):
        if not FinancialData._initialized:
            self.file_path = file_path
            self.data = self._load_data()
            FinancialData._initialized = True

    def _load_data(self) -> Dict:
        """Load JSON data from file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {"budgets": [], "transactions": []}

    def _save_data(self) -> None:
        """Save current data to JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_budget(self, year: int, month: int, tags: List[Dict] = None) -> None:
        """Add a new budget for a specific month/year."""
        if tags is None:
            tags = []

        # Check if budget already exists
        for budget in self.data["budgets"]:
            if budget["year"] == year and budget["month"] == month:
                raise ValueError(f"Budget for {year}-{month} already exists")

        new_budget = {
            "year": year,
            "month": month,
            "tags": tags
        }
        self.data["budgets"].append(new_budget)
        self._save_data()

    def add_tag(self, year: int, month: int, tag_id: str, name: str,
                max_amount: float, sub_tags: List[Dict] = None) -> None:
        """Add a new tag to a specific budget."""
        if sub_tags is None:
            sub_tags = []

        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        # Check if tag already exists
        for tag in budget["tags"]:
            if tag["id"] == tag_id:
                raise ValueError(f"Tag '{tag_id}' already exists")

        new_tag = {
            "id": tag_id,
            "name": name,
            "maxAmount": max_amount,
            "subTags": sub_tags
        }
        budget["tags"].append(new_tag)
        self._save_data()

    def add_subtag(self, year: int, month: int, parent_tag_id: str,
                   subtag_id: str, name: str, max_amount: float) -> None:
        """Add a subtag to a parent tag."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        parent_tag = self._get_tag(budget, parent_tag_id)
        if parent_tag is None:
            raise ValueError(f"Parent tag '{parent_tag_id}' not found")

        # Check if subtag already exists
        for subtag in parent_tag["subTags"]:
            if subtag["id"] == subtag_id:
                raise ValueError(f"Subtag '{subtag_id}' already exists")

        new_subtag = {
            "id": subtag_id,
            "name": name,
            "maxAmount": max_amount
        }
        parent_tag["subTags"].append(new_subtag)
        self._save_data()

    def remove_budget(self, year: int, month: int) -> None:
        """Remove a budget for a specific month/year."""
        self.data["budgets"] = [
            b for b in self.data["budgets"]
            if not (b["year"] == year and b["month"] == month)
        ]
        self._save_data()

    def remove_tag(self, year: int, month: int, tag_id: str) -> None:
        """Remove a tag from a specific budget."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        budget["tags"] = [t for t in budget["tags"] if t["id"] != tag_id]
        self._save_data()

    def remove_subtag(self, year: int, month: int, parent_tag_id: str,
                     subtag_id: str) -> None:
        """Remove a subtag from a parent tag."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        parent_tag = self._get_tag(budget, parent_tag_id)
        if parent_tag is None:
            raise ValueError(f"Parent tag '{parent_tag_id}' not found")

        parent_tag["subTags"] = [
            st for st in parent_tag["subTags"] if st["id"] != subtag_id
        ]
        self._save_data()

    def edit_budget(self, year: int, month: int, new_tags: List[Dict]) -> None:
        """Edit an existing budget's tags."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        budget["tags"] = new_tags
        self._save_data()

    def edit_tag(self, year: int, month: int, tag_id: str,
                 name: Optional[str] = None, max_amount: Optional[float] = None) -> None:
        """Edit a tag's properties."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        tag = self._get_tag(budget, tag_id)
        if tag is None:
            raise ValueError(f"Tag '{tag_id}' not found")

        if name is not None:
            tag["name"] = name
        if max_amount is not None:
            tag["maxAmount"] = max_amount

        self._save_data()

    def edit_subtag(self, year: int, month: int, parent_tag_id: str,
                    subtag_id: str, name: Optional[str] = None,
                    max_amount: Optional[float] = None) -> None:
        """Edit a subtag's properties."""
        budget = self._get_budget(year, month)
        if budget is None:
            raise ValueError(f"Budget for {year}-{month} not found")

        parent_tag = self._get_tag(budget, parent_tag_id)
        if parent_tag is None:
            raise ValueError(f"Parent tag '{parent_tag_id}' not found")

        subtag = self._get_subtag(parent_tag, subtag_id)
        if subtag is None:
            raise ValueError(f"Subtag '{subtag_id}' not found")

        if name is not None:
            subtag["name"] = name
        if max_amount is not None:
            subtag["maxAmount"] = max_amount

        self._save_data()

    def get_budget(self, year: int, month: int) -> Optional[Dict]:
        """Get budget data for a specific month/year."""
        return self._get_budget(year, month)

    def get_all_budgets(self) -> List[Dict]:
        """Get all budgets."""
        return self.data["budgets"]

    # Transaction methods
    def add_transaction(self, transaction_id: str, year: int, month: int, day: int,
                       amount: float, description: str, tag_id: str,
                       subtag_id: Optional[str] = None) -> None:
        """Add a new transaction."""
        # Check if transaction ID already exists
        for transaction in self.data["transactions"]:
            if transaction["id"] == transaction_id:
                raise ValueError(f"Transaction with id '{transaction_id}' already exists")

        new_transaction = {
            "id": transaction_id,
            "year": year,
            "month": month,
            "day": day,
            "amount": amount,
            "description": description,
            "tagId": tag_id,
            "subtagId": subtag_id
        }
        self.data["transactions"].append(new_transaction)
        self._save_data()

    def remove_transaction(self, transaction_id: str) -> None:
        """Remove a transaction by ID."""
        self.data["transactions"] = [
            t for t in self.data["transactions"] if t["id"] != transaction_id
        ]
        self._save_data()

    def edit_transaction(self, transaction_id: str, year: Optional[int] = None,
                        month: Optional[int] = None, day: Optional[int] = None,
                        amount: Optional[float] = None, description: Optional[str] = None,
                        tag_id: Optional[str] = None, subtag_id: Optional[str] = None) -> None:
        """Edit a transaction's properties."""
        transaction = self._get_transaction(transaction_id)
        if transaction is None:
            raise ValueError(f"Transaction with id '{transaction_id}' not found")

        if year is not None:
            transaction["year"] = year
        if month is not None:
            transaction["month"] = month
        if day is not None:
            transaction["day"] = day
        if amount is not None:
            transaction["amount"] = amount
        if description is not None:
            transaction["description"] = description
        if tag_id is not None:
            transaction["tagId"] = tag_id
        if subtag_id is not None:
            transaction["subtagId"] = subtag_id

        self._save_data()

    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get a transaction by ID."""
        return self._get_transaction(transaction_id)

    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions."""
        return self.data["transactions"]

    def get_transactions_by_date(self, year: int, month: Optional[int] = None,
                                 day: Optional[int] = None) -> List[Dict]:
        """Get transactions filtered by date."""
        transactions = [t for t in self.data["transactions"] if t["year"] == year]

        if month is not None:
            transactions = [t for t in transactions if t["month"] == month]

        if day is not None:
            transactions = [t for t in transactions if t["day"] == day]

        return transactions

    def get_transactions_by_tag(self, tag_id: str, subtag_id: Optional[str] = None) -> List[Dict]:
        """Get transactions filtered by tag."""
        transactions = [t for t in self.data["transactions"] if t["tagId"] == tag_id]

        if subtag_id is not None:
            transactions = [t for t in transactions if t.get("subtagId") == subtag_id]

        return transactions

    # Helper methods
    def _get_budget(self, year: int, month: int) -> Optional[Dict]:
        """Helper method to find a budget."""
        for budget in self.data["budgets"]:
            if budget["year"] == year and budget["month"] == month:
                return budget
        return None

    def _get_tag(self, budget: Dict, tag_id: str) -> Optional[Dict]:
        """Helper method to find a tag in a budget."""
        for tag in budget["tags"]:
            if tag["id"] == tag_id:
                return tag
        return None

    def _get_subtag(self, parent_tag: Dict, subtag_id: str) -> Optional[Dict]:
        """Helper method to find a subtag in a parent tag."""
        for subtag in parent_tag["subTags"]:
            if subtag["id"] == subtag_id:
                return subtag
        return None

    def _get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Helper method to find a transaction by ID."""
        for transaction in self.data["transactions"]:
            if transaction["id"] == transaction_id:
                return transaction
        return None
