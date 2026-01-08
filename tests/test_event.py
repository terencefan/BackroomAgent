import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.utils.dice import Dice
from backroom_agent.utils.event import Event

class MockDice(Dice):
    """Mocks dice rolls for deterministic testing."""
    def __init__(self, val):
        # Initialize parent with a dummy seed, though we won't use it
        super().__init__(seed=0)
        self.val = val

    def d20(self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> int:
        return self.val

    def d100(self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> int:
        return self.val

class TestEvent(unittest.TestCase):
    def test_d20_event_ranges(self):
        # Create an event: "Climb Wall"
        # 1-10: Fall
        # 11-19: Succeed
        # 20: Perfect
        evt = Event("Climb Wall", "d20")
        evt.add_outcome("Fall", 1, 10)
        evt.add_outcome("Succeed", 11, 19)
        evt.add_outcome("Perfect", 20)
        
        # Test Fall outcome (using value 5)
        roll, res = evt.resolve(MockDice(5))
        self.assertEqual(roll, 5)
        self.assertEqual(res, "Fall")
        
        # Test Succeed outcome (using value 15)
        roll, res = evt.resolve(MockDice(15))
        self.assertEqual(roll, 15)
        self.assertEqual(res, "Succeed")
        
        # Test Perfect outcome (using value 20)
        roll, res = evt.resolve(MockDice(20))
        self.assertEqual(roll, 20)
        self.assertEqual(res, "Perfect")

    def test_outcome_gaps(self):
        """Test what happens when a roll falls in a gap."""
        evt = Event("Search", "d100")
        evt.add_outcome("Found Nothing", 1, 50)
        evt.add_outcome("Found Gold", 60, 100)
        # 51-59 is undefined
        
        roll, res = evt.resolve(MockDice(55))
        self.assertEqual(roll, 55)
        self.assertIsNone(res)

    def test_invalid_die_type(self):
        with self.assertRaises(ValueError):
            Event("Bad Event", "d6")

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        evt = Event("Encounter", "d20")
        evt.add_outcome("Goblin", 1, 10)
        evt.add_outcome("Dragon", 20)
        
        json_str = evt.to_json()
        restored_evt = Event.from_json(json_str)
        
        self.assertEqual(restored_evt.name, "Encounter")
        self.assertEqual(restored_evt.die_type, "d20")
        self.assertEqual(len(restored_evt.outcomes), 2)
        
        # Check first outcome
        (min1, max1), res1 = restored_evt.outcomes[0]
        self.assertEqual(min1, 1)
        self.assertEqual(max1, 10)
        self.assertEqual(res1, "Goblin")
        
        # Check second outcome
        (min2, max2), res2 = restored_evt.outcomes[1]
        self.assertEqual(min2, 20)
        self.assertEqual(max2, 20)
        self.assertEqual(res2, "Dragon")

if __name__ == '__main__':
    unittest.main()
