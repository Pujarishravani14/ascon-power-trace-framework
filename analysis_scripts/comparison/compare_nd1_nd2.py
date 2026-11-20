import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

output = Path("nd1_nd2_comparison")
output.mkdir(exist_ok=True)

# --------------------------------
# ND=1 experimental results
# --------------------------------

nd1 = {
    "index": [
        1, 2, 5, 8, 11, 12, 15, 18, 19, 22, 25,
        28, 29, 32, 35, 39, 42, 45, 49, 52, 55, 59, 62
    ],
    "expected_rank": [
        2, 3, 1, 2, 1, 1, 7, 4, 2, 4, 1,
        2, 1, 4, 6, 1, 2, 1, 4, 5, 6, 3, 5
    ]
}

# --------------------------------
# ND=2 experimental results
# --------------------------------

nd2 = {
    "index": [
        2, 8, 11, 12, 15, 18, 19, 22, 25, 28, 29,
        32, 35, 39, 42, 45, 49, 52, 55, 59, 62
    ],
    "expected_rank": [
        10, 39, 1, 19, 50, 33, 43, 19, 59, 5, 45,
        16, 59, 24, 49, 35, 59, 61, 43, 11, 13
    ]
}

# --------------------------------
# Summary calculation
# --------------------------------

def calculate_metrics(data, bit_accuracy):
    ranks = data["expected_rank"]

    return {
        "Indices": len(ranks),
        "Traces per index": 100000,
        "Mean expected rank": round(sum(ranks) / len(ranks), 2),
        "Top-1": f"{sum(r == 1 for r in ranks)}/{len(ranks)}",
        "Top-5": f"{sum(r <= 5 for r in ranks)}/{len(ranks)}",
        "Top-10": f"{sum(r <= 10 for r in ranks)}/{len(ranks)}",
        "Key-bit accuracy (%)": bit_accuracy,
        "Exact k0 recovery": "No"
    }

comparison = pd.DataFrame(
    {
        "nd=1": calculate_metrics(nd1, 64.06),
        "nd=2": calculate_metrics(nd2, 56.25)
    }
)

print("\n========== ND=1 vs ND=2 COMPARISON ==========\n")
print(comparison.to_string())

comparison.to_csv(
    output / "nd1_nd2_comparison.csv"
)

# --------------------------------
# Separate expected-rank graphs
# --------------------------------

def plot_rank(data, title, filename):
    plt.figure(figsize=(13, 6))

    plt.bar(
        data["index"],
        data["expected_rank"],
        width=0.65
    )

    plt.axhline(
        y=1,
        linestyle="--",
        label="Correct candidate at rank 1"
    )

    plt.xlabel("Key index")
    plt.ylabel("Rank of expected candidate")
    plt.title(title)

    plt.xticks(data["index"])
    plt.yticks(range(1, 65, 5))
    plt.ylim(0, 65)
    plt.grid(axis="y", linestyle=":", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    plt.savefig(output / filename, dpi=300)
    plt.show()
    plt.close()

plot_rank(
    nd1,
    "ND=1: Expected Candidate Rank (100,000 traces)",
    "nd1_expected_rank.png"
)

plot_rank(
    nd2,
    "ND=2: Expected Candidate Rank (100,000 traces)",
    "nd2_expected_rank.png"
)

print("\nFiles saved in:", output.resolve())
print("1. nd1_nd2_comparison.csv")
print("2. nd1_expected_rank.png")
print("3. nd2_expected_rank.png")
