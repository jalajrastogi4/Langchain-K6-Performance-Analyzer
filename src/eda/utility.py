import random
import numpy as np

class StreamingStats:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0
        self.min_val = float("inf")
        self.max_val = float("-inf")

    def update(self, x: float):
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.M2 += delta * delta2
        self.min_val = min(self.min_val, x)
        self.max_val = max(self.max_val, x)

    @property
    def variance(self):
        return self.M2 / self.n if self.n > 1 else 0.0

    @property
    def stddev(self):
        return self.variance ** 0.5

    @property
    def avg(self):
        return self.mean

    @property
    def min(self):
        return self.min_val if self.n > 0 else None

    @property
    def max(self):
        return self.max_val if self.n > 0 else None


class ReservoirSampler:
    def __init__(self, size=50000):
        self.size = size
        self.sample = []
        self.count = 0

    def update(self, x: float):
        self.count += 1
        if len(self.sample) < self.size:
            self.sample.append(x)
        else:
            idx = random.randint(0, self.count - 1)
            if idx < self.size:
                self.sample[idx] = x

    def percentile(self, p: float):
        if not self.sample:
            return None
        return float(np.percentile(self.sample, p))