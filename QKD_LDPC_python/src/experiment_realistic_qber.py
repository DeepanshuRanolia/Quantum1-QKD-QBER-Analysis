
import error_correction_lib as ec
import numpy as np
from src.file_utils import codes_from_file
import csv

# Reproducibility
np.random.seed(42)

# Load the same LDPC codes as the original experiment
codes = codes_from_file("codes_1944.txt")
n = 1944

# Experimental settings
qber_values = [0.02, 0.05, 0.08]
n_tries = 5       # Initial pilot: 20 trials per QBER
f_start = 1.0

# Store results separately
output_file = "realistic_qber_results.csv"

R_range = [code[0] for code in codes]

print("Available LDPC code rates:", np.sort(R_range))
print("Block length:", n)
print("Trials per QBER:", n_tries)

results = []

for qber in qber_values:

    print("\n------------------------------")
    print(f"Testing QBER = {qber:.2%}")
    print("------------------------------")

    try:
        (
            f_mean,
            com_iters_mean,
            R,
            s_n,
            p_n,
            p_n_max,
            k_n,
            discl_n,
            FER
        ) = ec.test_ec(
            qber,
            R_range,
            codes,
            n,
            n_tries,
            f_start=f_start,
            show=0,
            discl_k=1
        )

        row = [
            n,
            n_tries,
            qber,
            f_mean,
            com_iters_mean,
            R,
            s_n,
            p_n,
            p_n_max,
            k_n,
            discl_n,
            FER
        ]

        results.append(row)

        print(f"Selected code rate: {R}")
        print(f"Mean efficiency: {f_mean:.5f}")
        print(f"Mean communication rounds: {com_iters_mean:.2f}")
        print(f"Frame error rate: {FER:.5f}")

    except Exception as error:
        print(f"Experiment failed at QBER {qber:.2%}: {error}")

# Save results
header = [
    "block_length",
    "trials",
    "qber",
    "efficiency",
    "communication_rounds",
    "code_rate",
    "shortened_bits",
    "punctured_bits",
    "max_punctured_bits",
    "remaining_key_bits",
    "disclosed_bits_per_round",
    "FER"
]

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(results)

print("\nExperiment completed.")
print("Results saved in:", output_file)
