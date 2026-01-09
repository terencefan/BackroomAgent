import json
from typing import Any, Dict, Optional


class Item:
    """
    Represents an item in the user's inventory or an item definition.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        item_id: str = "",
        category: str = "General",
        quantity: int = 1,
    ):
        self.name = name
        self.description = description
        self.item_id = item_id if item_id else name.lower().replace(" ", "_")
        self.category = category
        self.quantity = quantity

    def to_dict(self, include_quantity: bool = True) -> Dict[str, Any]:
        """Convert the item to a dictionary for serialization."""
        data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "id": self.item_id,
            "category": self.category,
        }
        if include_quantity:
            data["quantity"] = self.quantity
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        """Create an Item instance from a dictionary."""
        return cls(
            name=data.get("name", "Unknown Item"),
            description=data.get("description", ""),
            item_id=data.get("id", ""),
            category=data.get("category", "General"),
            quantity=data.get("quantity", 1),
        )

    def to_json(self, include_quantity: bool = True) -> str:
        """Serialize the item to a JSON string."""
        return json.dumps(
            self.to_dict(include_quantity=include_quantity),
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Item":
        """Create an Item instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
