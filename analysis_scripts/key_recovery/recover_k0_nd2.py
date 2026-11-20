import pickle
import numpy as np
from pathlib import Path

# Known key, used only to evaluate the recovered result
actual_k0 = int("82be0b6a9dd8112f", 16)

indices = [
    2, 8, 11, 12, 15, 18, 19, 22, 25, 28, 29,
    32, 35, 39, 42, 45, 49, 52, 55, 59, 62
]

root = Path(
    "protected-bi32-armv6/checkpoints_2nov_fixed100000_nd2_seed42/"
    "k0/z0/b2"
)

# Accumulated evidence for every bit of k0
log_evidence = np.zeros((64, 2), dtype=np.float64)
coverage = np.zeros(64, dtype=int)

def extract_positions(i0):
    i1 = (i0 + 36) % 64
    i2 = (i0 + 45) % 64

    positions = []

    for i in range(2):
        positions.append((i + i0) % 64)
    for i in range(2):
        positions.append((i + i1) % 64)
    for i in range(2):
        positions.append((i + i2) % 64)

    return positions

def softmax(x):
    x = x - np.max(x)
    e = np.exp(x)
    return e / np.sum(e)

print("Loading final CPA checkpoints...")

for idx in indices:
    path = root / f"{idx:02d}" / "00" / "0100000.pkl"

    with open(path, "rb") as f:
        data = pickle.load(f)

    rho = data["rho"]
    scores = np.nanmax(np.abs(rho), axis=1)

    # Standardize scores within this index
    std = np.std(scores)
    if std == 0:
        raise ValueError(f"Zero score variation at index {idx}")

    normalized = (scores - np.mean(scores)) / std

    # Convert candidate scores into relative weights
    probabilities = softmax(normalized)

    positions = extract_positions(idx)

    # Each guess represents six bits of the key
    for guess in range(64):
        for j, pos in enumerate(positions):
            bit_value = (guess >> (5-j)) & 1
            log_evidence[pos, bit_value] += np.log(
                max(probabilities[guess], 1e-300)
            )

    for pos in positions:
        coverage[pos] += 1

# Construct candidate key from accumulated bit evidence
recovered_k0 = 0

print("\n===== KEY BIT ANALYSIS =====")
print("Bit | Coverage | Evidence for 0 | Evidence for 1 | Recovered")

for pos in range(64):
    if coverage[pos] == 0:
        print(f"{pos:3d} | NOT COVERED")
        continue

    bit_value = int(np.argmax(log_evidence[pos]))
    recovered_k0 |= bit_value << (63-pos)

    print(
        f"{pos:3d} | {coverage[pos]:8d} | "
        f"{log_evidence[pos,0]:14.5f} | "
        f"{log_evidence[pos,1]:14.5f} | {bit_value}"
    )

actual_bits = f"{actual_k0:064b}"
recovered_bits = f"{recovered_k0:064b}"

covered = coverage > 0
correct = sum(
    recovered_bits[i] == actual_bits[i]
    for i in range(64) if covered[i]
)

print("\n===== RECOVERY RESULT =====")
print(f"Actual k0:    {actual_k0:016x}")
print(f"Recovered k0: {recovered_k0:016x}")
print(f"Covered bits: {np.sum(covered)}/64")
print(f"Correct covered bits: {correct}/{np.sum(covered)}")

if np.all(covered):
    print(f"Bit accuracy: {correct/64*100:.2f}%")
    print(f"Exact key match: {recovered_k0 == actual_k0}")
else:
    print("Full 64-bit recovery cannot be established: some bits are uncovered.")
