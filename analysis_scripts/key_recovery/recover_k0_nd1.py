import pickle
import numpy as np
from pathlib import Path

# Used only to evaluate the result
actual_k0 = int("82be0b6a9dd8112f", 16)

indices = [
    1, 2, 5, 8, 11, 12, 15, 18, 19, 22, 25,
    28, 29, 32, 35, 39, 42, 45, 49, 52, 55, 59, 62
]

root = Path(
    "protected-bi32-armv6/checkpoints_2nov_fixed100000/"
    "k0/z0/b1"
)

log_evidence = np.zeros((64, 2), dtype=np.float64)
coverage = np.zeros(64, dtype=int)

def extract_positions(i0):
    return [
        i0 % 64,
        (i0 + 36) % 64,
        (i0 + 45) % 64
    ]

def softmax(x):
    x = x - np.max(x)
    e = np.exp(x)
    return e / np.sum(e)

print("Loading final nd=1 CPA checkpoints...")

for idx in indices:
    path = root / f"{idx:02d}" / "00" / "0100000.pkl"

    if not path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {path}")

    with open(path, "rb") as f:
        data = pickle.load(f)

    rho = data["rho"]

    if rho.shape[0] != 8:
        raise ValueError(
            f"Index {idx}: expected 8 guesses, got {rho.shape[0]}"
        )

    scores = np.nanmax(np.abs(rho), axis=1)

    std = np.std(scores)
    if std == 0:
        raise ValueError(f"Zero score variation at index {idx}")

    normalized = (scores - np.mean(scores)) / std
    probabilities = softmax(normalized)

    positions = extract_positions(idx)

    # Each nd=1 guess represents 3 key bits
    for guess in range(8):
        for j, pos in enumerate(positions):
            bit_value = (guess >> (2-j)) & 1
            log_evidence[pos, bit_value] += np.log(
                max(probabilities[guess], 1e-300)
            )

    for pos in positions:
        coverage[pos] += 1

recovered_k0 = 0

print("\n===== ND=1 KEY BIT ANALYSIS =====")
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

print("\n===== ND=1 RECOVERY RESULT =====")
print(f"Actual k0:    {actual_k0:016x}")
print(f"Recovered k0: {recovered_k0:016x}")
print(f"Covered bits: {np.sum(covered)}/64")
print(f"Correct covered bits: {correct}/{np.sum(covered)}")

if np.all(covered):
    print(f"Bit accuracy: {correct/64*100:.2f}%")
    print(f"Exact key match: {recovered_k0 == actual_k0}")
else:
    print("Full 64-bit recovery cannot be established: some bits are uncovered.")
