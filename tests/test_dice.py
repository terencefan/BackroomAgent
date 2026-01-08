import sys
import os
import unittest
import random

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.utils.dice import Dice

class TestDice(unittest.TestCase):
    def test_range(self):
        """Test that dice rolls stay within expected bounds."""
        d = Dice()
        for _ in range(100):
            res = d.d20()
            self.assertTrue(1 <= res <= 20, f"d20 result {res} out of range")
            res = d.d100()
            self.assertTrue(1 <= res <= 100, f"d100 result {res} out of range")

    def test_seed_reproducibility(self):
        """Test that same seed produces same sequence of rolls."""
        seed = "test_seed_reproducibility"
        d1 = Dice(seed)
        d2 = Dice(seed)
        
        # They should produce identical sequences
        for i in range(20):
            val1 = d1.d20()
            val2 = d2.d20()
            self.assertEqual(val1, val2, f" mismatch at roll {i}")

    def test_modifier_clamping(self):
        """Test that modifiers are applied and results are clamped."""
        d = Dice()
        
        # Modifier that should push it over 20 (clamped to 20)
        # We roll many times to be sure we aren't just getting lucky with a low roll + huge mod
        for _ in range(10):
            res = d.d20(modifier=100)
            self.assertEqual(res, 20, "Should clamp to 20")

        # Modifier that should push it below 1 (clamped to 1)
        for _ in range(10):
            res = d.d20(modifier=-100)
            self.assertEqual(res, 1, "Should clamp to 1")

        # Test valid modifier within range
        # Use a fixed seed to check math
        # Seed 42 sequence for d20 seems to start with:
        # We can just verify it stays in bounds for valid modifiers
        res = d.d20(modifier=2)
        self.assertTrue(1 <= res <= 20)

    def test_advantage_logic(self):
        """Test advantage logic with fixed seed."""
        seed = 42
        # Use python's random to predict expectations
        rng = random.Random(seed)
        v1 = rng.randint(1, 20)
        v2 = rng.randint(1, 20)
        expected_adv = max(v1, v2)
        expected_dis = min(v1, v2)

        # Test Advantage
        d_adv = Dice(seed=seed)
        res_adv = d_adv.d20(advantage=True)
        self.assertEqual(res_adv, expected_adv, "Advantage should take the higher of the first two rolls")

        # Test Disadvantage
        # Need to re-init rng locally to get same sequence
        rng = random.Random(seed)
        v1 = rng.randint(1, 20)
        v2 = rng.randint(1, 20)
        expected_dis = min(v1, v2)

        d_dis = Dice(seed=seed)
        res_dis = d_dis.d20(disadvantage=True)
        self.assertEqual(res_dis, expected_dis, "Disadvantage should take the lower of the first two rolls")

    def test_advantage_disadvantage_cancel(self):
        """Test that advantage and disadvantage cancel each other out."""
        seed = 12345
        rng = random.Random(seed)
        expected_val = rng.randint(1, 20)

        d = Dice(seed=seed)
        # Should behave like a normal single roll
        res = d.d20(advantage=True, disadvantage=True)
        self.assertEqual(res, expected_val, "Advantage and Disadvantage should cancel out")

if __name__ == '__main__':
    unittest.main()
