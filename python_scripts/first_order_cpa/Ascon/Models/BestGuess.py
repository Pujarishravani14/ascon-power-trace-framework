from dataclasses import dataclass


@dataclass
class BestGuess:
    correlation: float = 0
    k0: int = 0
    k1: int = 0
    k2: int = 0

    def update(self, correlation, k0, k1, k2):
        self.correlation = correlation
        self.k0 = k0
        self.k1 = k1
        self.k2 = k2
