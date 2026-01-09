import random
import time
import uuid


class Dice:
    """A utility class for rolling dice with reproducible seeds."""

    def __init__(self, seed: int | str = None):
        if seed is None:
            # Default seed using MAC address + timestamp
            mac = uuid.getnode()
            timestamp = time.time_ns()
            seed = f"{mac}_{timestamp}"

        self.seed = seed
        self._index = 0
        self._rng = random.Random(seed)

    def roll(
        self,
        sides: int,
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> int:
        """
        Roll a die with the specified number of sides.
        Supports:
        - Modifier: Added to the roll result.
        - Advantage/Disadvantage (D&D 5e rules).
        - Clamping: Result is clamped between 1 and sides.
        """
        if advantage and disadvantage:
            advantage = False
            disadvantage = False

        if advantage:
            r1 = self._roll_once(sides)
            r2 = self._roll_once(sides)
            base_roll = max(r1, r2)
        elif disadvantage:
            r1 = self._roll_once(sides)
            r2 = self._roll_once(sides)
            base_roll = min(r1, r2)
        else:
            base_roll = self._roll_once(sides)

        total = base_roll + modifier
        # Clamp result between 1 and max sides
        return max(1, min(sides, total))

    def _roll_once(self, sides: int) -> int:
        """Helper to roll a single die and increment index."""
        self._index += 1
        return self._rng.randint(1, sides)

    def d20(
        self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False
    ) -> int:
        """Roll a 20-sided die."""
        return self.roll(
            20, modifier=modifier, advantage=advantage, disadvantage=disadvantage
        )

    def d6(
        self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False
    ) -> int:
        """Roll a 6-sided die."""
        return self.roll(
            6, modifier=modifier, advantage=advantage, disadvantage=disadvantage
        )

    def d100(
        self, modifier: int = 0, advantage: bool = False, disadvantage: bool = False
    ) -> int:
        """Roll a 100-sided die."""
        return self.roll(
            100, modifier=modifier, advantage=advantage, disadvantage=disadvantage
        )
