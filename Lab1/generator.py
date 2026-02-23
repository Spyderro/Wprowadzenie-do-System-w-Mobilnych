import math
import random
import matplotlib.pyplot as plt

def generate_poisson(lam, n, seed=None):
    if seed is not None:
        random.seed(seed)
    samples = []
    q = math.exp(-lam) # [cite: 81]
    for _ in range(n):
        X = -1
        S = 1.0
        while S > q: # [cite: 82]
            U = random.random() # GenU(0,1) [cite: 85]
            S = S * U # [cite: 86]
            X += 1
        samples.append(X)
    return samples

def generate_normal(mu, sigma, n, seed=None):
    if seed is not None:
        random.seed(seed)
    samples = []
    for _ in range(n // 2):
        u1 = random.random() # [cite: 160]
        u2 = random.random()
        # Metoda Boxa-Mullera [cite: 162]
        common = math.sqrt(-2.0 * math.log(u1))
        z0 = common * math.cos(2.0 * math.pi * u2)
        z1 = common * math.sin(2.0 * math.pi * u2)
        # Skalowanie do N(mu, sigma)
        samples.append(mu + sigma * z0)
        samples.append(mu + sigma * z1)
    return samples

l_param = 4.0
mu_param = 10.0
sigma = 2.0
n_samples = 10000
Seed = 42

data_p = generate_poisson(l_param, n_samples, seed=Seed)
data_n = generate_normal(mu_param, sigma, n_samples, seed=Seed)

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
bins_p = [i - 0.5 for i in range(min(data_p), max(data_p) + 2)]
plt.hist(data_p, bins=bins_p, density=True, color='blue', edgecolor='black')
plt.title(f"Rozkład Poissona")

plt.subplot(1, 2, 2)
plt.hist(data_n, bins=40, density=True, color='red', edgecolor='black')
plt.title(f"Rozkład Normalny")

plt.tight_layout()
plt.show()