
import csv
import time
import numpy as np

# Import existing functions from your working implementation
from src.bb84_ldpc_integration import (
    bb84_simulation,
    hamming_reconciliation,
    bch_reconciliation,
    ldpc_reconciliation_full
)

from src.file_utils import codes_from_file


# ============================================================
# 1. EXPERIMENT SETTINGS
# ============================================================

QBER_VALUES = [0.01, 0.02, 0.03, 0.05, 0.08, 0.10]

TRIALS = 3

TOTAL_TRANSMISSIONS = 30000

SAMPLE_SIZE = 1000

OUTPUT_FILE = "qber_experiment_results.csv"


# ============================================================
# 2. RUN ONE EXPERIMENT
# ============================================================

def run_one_experiment(channel_qber, trial, codes):

    print("\n" + "=" * 70)
    print(f"QBER: {channel_qber * 100:.1f}% | Trial: {trial}")
    print("=" * 70)

    # Generate BB84 keys
    alice_key, bob_key, qber_est = bb84_simulation(
        N=TOTAL_TRANSMISSIONS,
        channel_qber=channel_qber,
        sample_size=SAMPLE_SIZE
    )

    initial_errors = int(np.sum(alice_key != bob_key))

    print("Estimated QBER:", qber_est)
    print("Sifted key length after sampling:", len(alice_key))
    print("Initial errors:", initial_errors)

    # All three methods receive the SAME keys
    methods = {
        "Hamming": lambda: hamming_reconciliation(
            alice_key, bob_key, qber_est
        ),

        "BCH": lambda: bch_reconciliation(
            alice_key, bob_key, qber_est
        ),

        "LDPC": lambda: ldpc_reconciliation_full(
            alice_key, bob_key, qber_est, codes
        )
    }

    trial_results = []

    # Run each reconciliation method
    for method_name, method_function in methods.items():

        print(f"\nRunning {method_name}...")

        try:
            result = method_function()

            row = {
                "trial": trial,
                "channel_qber": channel_qber,
                "estimated_qber": qber_est,
                "initial_errors": initial_errors,
                "method": method_name,
                "processed_bits": result["processed_bits"],
                "remaining_bits": result["remaining_bits"],
                "total_blocks": result["total_blocks"],
                "failed_blocks": result["failed_blocks"],
                "disclosed_bits": result["disclosed_bits"],
                "efficiency": result["efficiency"],
                "execution_time": result["execution_time"],
                "key_agreement": result["key_agreement"],
                "status": "Success",
                "error_message": ""
            }

            print("Agreement:", result["key_agreement"])
            print("Failed blocks:", result["failed_blocks"])
            print("Efficiency:", result["efficiency"])
            print("Execution time:", result["execution_time"])

        except Exception as error:

            print(f"{method_name} failed: {error}")

            row = {
                "trial": trial,
                "channel_qber": channel_qber,
                "estimated_qber": qber_est,
                "initial_errors": initial_errors,
                "method": method_name,
                "processed_bits": 0,
                "remaining_bits": 0,
                "total_blocks": 0,
                "failed_blocks": 0,
                "disclosed_bits": 0,
                "efficiency": float("nan"),
                "execution_time": float("nan"),
                "key_agreement": False,
                "status": "Failed",
                "error_message": str(error)
            }

        trial_results.append(row)

    return trial_results


# ============================================================
# 3. RUN ALL QBER EXPERIMENTS
# ============================================================

def run_qber_experiments():

    # Fix random seed for reproducibility
    np.random.seed(42)

    print("\nLoading LDPC codes...")

    codes = codes_from_file("codes_1944.txt")

    print("LDPC codes loaded successfully.")

    all_results = []

    total_experiments = len(QBER_VALUES) * TRIALS
    experiment_number = 0

    start_time = time.perf_counter()

    for qber in QBER_VALUES:

        for trial in range(1, TRIALS + 1):

            experiment_number += 1

            print(
                f"\nExperiment {experiment_number}/{total_experiments}"
            )

            trial_results = run_one_experiment(
                channel_qber=qber,
                trial=trial,
                codes=codes
            )

            all_results.extend(trial_results)

    total_time = time.perf_counter() - start_time

    # ========================================================
    # 4. SAVE RESULTS TO CSV
    # ========================================================

    if all_results:

        fieldnames = list(all_results[0].keys())

        with open(
            OUTPUT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames
            )

            writer.writeheader()
            writer.writerows(all_results)

    print("\n" + "=" * 70)
    print("ALL EXPERIMENTS COMPLETED")
    print("=" * 70)

    print("Total experiments:", total_experiments)
    print("Total result rows:", len(all_results))
    print("Results saved to:", OUTPUT_FILE)
    print("Total execution time:", round(total_time, 2), "seconds")


# ============================================================
# 5. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_qber_experiments()
