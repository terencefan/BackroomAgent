import json
from typing import List, Tuple, Any, Optional, Dict
from backroom_agent.utils.dice import Dice

class Event:
    """
    Represents a game event determined by a dice roll.
    """
    def __init__(self, name: str, die_type: str = 'd20'):
        if die_type not in ['d20', 'd100']:
            raise ValueError("die_type must be 'd20' or 'd100'")
        
        self.name = name
        self.die_type = die_type
        # List of ((min, max), result_data)
        self.outcomes: List[Tuple[Tuple[int, int], Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return {
            "name": self.name,
            "die_type": self.die_type,
            "outcomes": [
                {"range": [min_v, max_v], "result": result}
                for (min_v, max_v), result in self.outcomes
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event instance from a dictionary."""
        event = cls(name=data["name"], die_type=data["die_type"])
        for outcome in data["outcomes"]:
            min_v, max_v = outcome["range"]
            
            # Support both old string format and new dict format
            result_data = outcome["result"]
            if isinstance(result_data, str):
                result_data = {"content": result_data}
                
            event.add_outcome(result_data, min_v, max_v)
        return event

    def to_json(self) -> str:
        """Serialize the event to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create an Event instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def add_outcome(self, result: Any, min_val: int, max_val: Optional[int] = None):
        """
        Add an outcome for a range of roll values.
        If max_val is None, it defaults to min_val (single value).
        """
        if max_val is None:
            max_val = min_val
        self.outcomes.append(((min_val, max_val), result))
        # Sort by min_val for consistency
        self.outcomes.sort(key=lambda x: x[0][0])

    def resolve(self, dice: Dice, modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> Tuple[int, Any]:
        """
        Rolls the dice and returns the (roll_total, result).
        If no outcome matches, returns (roll_total, None).
        """
        if self.die_type == 'd20':
            roll = dice.d20(modifier=modifier, advantage=advantage, disadvantage=disadvantage)
        else:
            roll = dice.d100(modifier=modifier, advantage=advantage, disadvantage=disadvantage)

        for (min_v, max_v), result in self.outcomes:
            if min_v <= roll <= max_v:
                return roll, result
        
        return roll, None
