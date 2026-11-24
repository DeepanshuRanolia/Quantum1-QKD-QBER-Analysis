
import time
import numpy as np

import error_correction_lib as ec
from src.file_utils import codes_from_file


# ============================================================
# 1. BB84 SIMULATION
# ============================================================

def bb84_simulation(N=30000, channel_qber=0.02, sample_size=1000):

    alice_bits = np.random.randint(0, 2, N)
    alice_bases = np.random.randint(0, 2, N)
    bob_bases = np.random.randint(0, 2, N)

    channel_errors = (
        np.random.random(N) < channel_qber
    ).astype(np.uint8)

    bob_bits = alice_bits ^ channel_errors

    # Basis sifting
    matched = alice_bases == bob_bases

    alice_sifted = alice_bits[matched]
    bob_sifted = bob_bits[matched]

    if sample_size >= len(alice_sifted):
        raise ValueError("Sample size too large.")

    # QBER estimation
    sample_indices = np.random.choice(
        len(alice_sifted),
        sample_size,
        replace=False
    )

    qber_est = np.mean(
        alice_sifted[sample_indices] !=
        bob_sifted[sample_indices]
    )

    # Remove disclosed sample bits
    keep = np.ones(len(alice_sifted), dtype=bool)
    keep[sample_indices] = False

    alice_key = alice_sifted[keep].astype(np.uint8)
    bob_key = bob_sifted[keep].astype(np.uint8)

    return alice_key, bob_key, qber_est


# ============================================================
# 2. COMMON FUNCTIONS
# ============================================================

def binary_entropy(p):

    if p <= 0 or p >= 1:
        return 0.0

    return -p * np.log2(p) - (1-p) * np.log2(1-p)


# ============================================================
# 3. HAMMING (7,4)
# ============================================================
def hamming_syndrome(block):
    """
    Calculate the syndrome for a Hamming(7,4) block.

    Input: 7-bit binary array
    Output: Integer syndrome from 0 to 7
    """

    H = np.array([
        [1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 1]
    ])

    block = np.array(block, dtype=int)

    syndrome = np.dot(H, block) % 2

    return int(
        syndrome[0] * 1 +
        syndrome[1] * 2 +
        syndrome[2] * 4
    )

def hamming_reconciliation(alice_key, bob_key, qber_est):

    start_time = time.perf_counter()

    n = min(len(alice_key), len(bob_key))

    num_blocks = n // 7
    processed_bits = num_blocks * 7
    remaining_bits = n - processed_bits

    alice = np.asarray(
        alice_key[:processed_bits], dtype=np.uint8
    ).reshape(num_blocks, 7)

    bob = np.asarray(
        bob_key[:processed_bits], dtype=np.uint8
    ).reshape(num_blocks, 7).copy()

    # Calculate error weights before correction
    error_weights = np.sum(alice != bob, axis=1)

    zero_error_blocks = int(np.sum(error_weights == 0))
    one_error_blocks = int(np.sum(error_weights == 1))
    multiple_error_blocks = int(np.sum(error_weights >= 2))

    corrected_blocks = 0

    # Store information about every block
    block_diagnostics = []

    for i in range(num_blocks):

        # Calculate syndromes
        alice_syn = hamming_syndrome(alice[i])
        bob_syn = hamming_syndrome(bob[i])

        error_syn = alice_syn ^ bob_syn

        correction_applied = False

        # Apply Hamming correction
        if 1 <= error_syn <= 7:

            bob[i, error_syn - 1] ^= 1
            corrected_blocks += 1
            correction_applied = True

        # Check whether correction was successful
        block_success = np.array_equal(alice[i], bob[i])

        # Record block information
        block_diagnostics.append({

            "method": "Hamming",

            "block_index": i,

            "error_weight": int(error_weights[i]),

            "success": bool(block_success),

            "correction_applied": correction_applied,

            "correction_weight": int(correction_applied)

        })

    failed_blocks = int(
        np.sum(np.any(alice != bob, axis=1))
    )

    successful_blocks = num_blocks - failed_blocks

    disclosed_bits = 3 * num_blocks

    h2 = binary_entropy(qber_est)

    efficiency = (
        disclosed_bits / (processed_bits * h2)
        if h2 > 0 else float("inf")
    )

    execution_time = time.perf_counter() - start_time

    corrected_bob = bob.flatten()

    return {

        "method": "Hamming (7,4)",

        "processed_bits": processed_bits,

        "remaining_bits": remaining_bits,

        "total_blocks": num_blocks,

        "corrected_blocks": corrected_blocks,

        "successful_blocks": successful_blocks,

        "failed_blocks": failed_blocks,

        "zero_error_blocks": zero_error_blocks,

        "one_error_blocks": one_error_blocks,

        "multiple_error_blocks": multiple_error_blocks,

        "block_diagnostics": block_diagnostics,

        "disclosed_bits": disclosed_bits,

        "efficiency": efficiency,

        "execution_time": execution_time,

        "key_agreement": bool(
            np.array_equal(alice.flatten(), corrected_bob)
        ),

        "corrected_bob": corrected_bob

    }


# ============================================================
# 4. BCH (15,7)
# ============================================================

BCH_GENERATOR = 0b111010001
BCH_N = 15
BCH_K = 7
BCH_T = 2


def polynomial_remainder(value, generator):

    while value.bit_length() >= generator.bit_length():

        shift = value.bit_length() - generator.bit_length()

        value ^= generator << shift

    return value


def block_to_integer(block):

    value = 0

    for i, bit in enumerate(block):

        if bit:
            value |= (1 << i)

    return value


def integer_to_error_pattern(value, length):

    return np.array(
        [(value >> i) & 1 for i in range(length)],
        dtype=np.uint8
    )


def build_bch_syndrome_table():

    syndrome_table = {}

    syndrome_table[0] = 0

    # Weight 1 errors
    for i in range(BCH_N):

        error = 1 << i

        syndrome = polynomial_remainder(
            error, BCH_GENERATOR
        )

        syndrome_table[syndrome] = error

    # Weight 2 errors
    for i in range(BCH_N):

        for j in range(i + 1, BCH_N):

            error = (1 << i) | (1 << j)

            syndrome = polynomial_remainder(
                error, BCH_GENERATOR
            )

            if syndrome in syndrome_table:

                raise ValueError(
                    "BCH syndrome collision detected."
                )

            syndrome_table[syndrome] = error

    return syndrome_table


BCH_SYNDROME_TABLE = build_bch_syndrome_table()



def bch_reconciliation(alice_key, bob_key, qber_est):

    start_time = time.perf_counter()

    n = min(len(alice_key), len(bob_key))

    num_blocks = n // BCH_N
    processed_bits = num_blocks * BCH_N
    remaining_bits = n - processed_bits

    alice = np.asarray(
        alice_key[:processed_bits], dtype=np.uint8
    ).reshape(num_blocks, BCH_N)

    bob = np.asarray(
        bob_key[:processed_bits], dtype=np.uint8
    ).reshape(num_blocks, BCH_N).copy()

    # Error distribution before correction
    error_weights = np.sum(alice != bob, axis=1)

    zero_error_blocks = int(np.sum(error_weights == 0))
    one_error_blocks = int(np.sum(error_weights == 1))
    two_error_blocks = int(np.sum(error_weights == 2))
    more_than_two_blocks = int(np.sum(error_weights > 2))

    corrected_blocks = 0
    uncorrectable_syndromes = 0

    failed_block_details = []

    # Store information about every BCH block
    block_diagnostics = []

    for i in range(num_blocks):

        alice_value = block_to_integer(alice[i])
        bob_value = block_to_integer(bob[i])

        # Actual error pattern before correction
        actual_error_pattern = alice[i] ^ bob[i]

        actual_error_positions = np.where(
            actual_error_pattern == 1
        )[0].tolist()

        actual_error_weight = len(actual_error_positions)

        # Calculate syndromes
        alice_syndrome = polynomial_remainder(
            alice_value, BCH_GENERATOR
        )

        bob_syndrome = polynomial_remainder(
            bob_value, BCH_GENERATOR
        )

        error_syndrome = alice_syndrome ^ bob_syndrome

        estimated_error_positions = []

        correction_applied = False

        # BCH decoding
        if error_syndrome != 0:

            if error_syndrome in BCH_SYNDROME_TABLE:

                error_value = BCH_SYNDROME_TABLE[
                    error_syndrome
                ]

                estimated_error_pattern = integer_to_error_pattern(
                    error_value, BCH_N
                )

                estimated_error_positions = np.where(
                    estimated_error_pattern == 1
                )[0].tolist()

                # Apply correction
                bob[i] ^= estimated_error_pattern

                corrected_blocks += 1
                correction_applied = True

            else:

                uncorrectable_syndromes += 1

        # Check corrected block
        block_success = np.array_equal(alice[i], bob[i])

        remaining_error_positions = np.where(
            alice[i] != bob[i]
        )[0].tolist()

        # Store failed block details
        if not block_success:

            failed_block_details.append({

                "block_index": i,

                "actual_error_weight": actual_error_weight,

                "actual_error_positions": actual_error_positions,

                "error_syndrome": error_syndrome,

                "estimated_error_positions": estimated_error_positions,

                "remaining_error_positions": remaining_error_positions

            })

        # Record every block, successful or failed
        block_diagnostics.append({

            "method": "BCH",

            "block_index": i,

            "error_weight": actual_error_weight,

            "success": bool(block_success),

            "correction_applied": correction_applied,

            "correction_weight": len(estimated_error_positions),

            "uncorrectable_syndrome": bool(
                error_syndrome != 0 and
                error_syndrome not in BCH_SYNDROME_TABLE
            )

        })

    failed_blocks = int(
        np.sum(np.any(alice != bob, axis=1))
    )

    successful_blocks = num_blocks - failed_blocks

    # BCH redundancy = 15 - 7 = 8 bits
    disclosed_bits = (BCH_N - BCH_K) * num_blocks

    h2 = binary_entropy(qber_est)

    efficiency = (
        disclosed_bits / (processed_bits * h2)
        if h2 > 0 else float("inf")
    )

    execution_time = time.perf_counter() - start_time

    corrected_bob = bob.flatten()

    return {

        "method": "BCH (15,7)",

        "processed_bits": processed_bits,

        "remaining_bits": remaining_bits,

        "total_blocks": num_blocks,

        "corrected_blocks": corrected_blocks,

        "successful_blocks": successful_blocks,

        "failed_blocks": failed_blocks,

        "zero_error_blocks": zero_error_blocks,

        "one_error_blocks": one_error_blocks,

        "two_error_blocks": two_error_blocks,

        "more_than_two_blocks": more_than_two_blocks,

        "uncorrectable_syndromes": uncorrectable_syndromes,

        "failed_block_details": failed_block_details,

        "block_diagnostics": block_diagnostics,

        "disclosed_bits": disclosed_bits,

        "efficiency": efficiency,

        "execution_time": execution_time,

        "key_agreement": bool(
            np.array_equal(alice.flatten(), corrected_bob)
        ),

        "corrected_bob": corrected_bob

    }


# ============================================================
# 5. LDPC RECONCILIATION
# ============================================================


def ldpc_reconciliation_full(
    alice_key,
    bob_key,
    qber_est,
    codes,
    n=1944
):

    start_time = time.perf_counter()

    alice_key = np.asarray(alice_key, dtype=np.uint8)
    bob_key = np.asarray(bob_key, dtype=np.uint8)

    total_bits = min(len(alice_key), len(bob_key))

    R_range = [code[0] for code in codes]

    R, s_n, p_n = ec.choose_sp(
        qber_est, 1.0, R_range, n
    )

    k_n = n - s_n - p_n

    if k_n <= 0:
        raise ValueError("Invalid LDPC input block length.")

    code_params = codes[(R, n)]

    s_y_joins = code_params["s_y_joins"]
    y_s_joins = code_params["y_s_joins"]
    punct_list = code_params["punct_list"]

    discl_n = int(round(n * (0.0280 - 0.02 * R)))

    num_blocks = total_bits // k_n

    processed_bits = num_blocks * k_n
    remaining_bits = total_bits - processed_bits

    if num_blocks == 0:
        raise ValueError("Not enough bits for an LDPC block.")

    corrected_blocks = 0
    failed_blocks = 0

    total_additional_disclosure = 0
    total_rounds = 0

    corrected_key_parts = []

    # Store information about every LDPC block
    block_diagnostics = []

    for block_index in range(num_blocks):

        start = block_index * k_n
        end = start + k_n

        alice_block = np.asarray(
            alice_key[start:end], dtype=int
        )

        bob_block = np.asarray(
            bob_key[start:end], dtype=int
        )

        # Actual errors before LDPC decoding
        actual_error_weight = int(
            np.sum(alice_block != bob_block)
        )

        # Run original LDPC decoder
        add_info, com_iters, error_pattern, ver_check = (
            ec.perform_ec(
                alice_block,
                bob_block,
                s_y_joins,
                y_s_joins,
                qber_est,
                s_n,
                p_n,
                punct_list=punct_list,
                discl_n=discl_n,
                show=0
            )
        )

        error_pattern = np.asarray(
            error_pattern, dtype=np.uint8
        )

        # Apply correction
        corrected_bob = (
            bob_block.astype(np.uint8) ^ error_pattern
        )

        corrected_key_parts.append(corrected_bob)

        # Calculate correction weight
        correction_weight = int(
            np.sum(error_pattern)
        )

        # Check corrected block
        block_success = np.array_equal(
            alice_block, corrected_bob
        )

        if block_success:
            corrected_blocks += 1
        else:
            failed_blocks += 1

        total_additional_disclosure += int(add_info)
        total_rounds += int(com_iters)

        # Record block-level information
        block_diagnostics.append({

            "method": "LDPC",

            "block_index": block_index,

            "error_weight": actual_error_weight,

            "success": bool(block_success),

            "correction_applied": bool(
                np.any(error_pattern)
            ),

            "correction_weight": correction_weight,

            "decoder_verification": bool(ver_check)

        })

    corrected_bob_key = np.concatenate(corrected_key_parts)

    m = (1 - R) * n

    h2 = binary_entropy(qber_est)

    total_disclosed_bits = (
        num_blocks * (m - p_n)
        + total_additional_disclosure
    )

    efficiency = (
        total_disclosed_bits / (processed_bits * h2)
        if h2 > 0 else float("inf")
    )

    execution_time = time.perf_counter() - start_time

    return {

        "method": "LDPC",

        "processed_bits": processed_bits,

        "remaining_bits": remaining_bits,

        "total_blocks": num_blocks,

        "corrected_blocks": corrected_blocks,

        "successful_blocks": corrected_blocks,

        "failed_blocks": failed_blocks,

        "code_rate": R,

        "shortened_bits": s_n,

        "punctured_bits": p_n,

        "input_bits_per_block": k_n,

        "disclosed_bits": int(total_disclosed_bits),

        "additional_disclosed_bits": total_additional_disclosure,

        "communication_rounds": total_rounds,

        "block_diagnostics": block_diagnostics,

        "efficiency": efficiency,

        "execution_time": execution_time,

        "key_agreement": failed_blocks == 0,

        "corrected_bob": corrected_bob_key

    }

def save_block_diagnostics(results, filename="block_error_results.csv"):

    import pandas as pd

    all_blocks = []

    for result in results:

        for block in result["block_diagnostics"]:

            all_blocks.append({

                "method": block["method"],

                "block_index": block["block_index"],

                "error_weight": block["error_weight"],

                "success": block["success"],

                "correction_applied": block["correction_applied"],

                "correction_weight": block["correction_weight"]

            })

    df = pd.DataFrame(all_blocks)

    df.to_csv(filename, index=False)

    print("\nBlock diagnostics saved to:", filename)

    print("\nFirst few records:")

    print(df.head(10).to_string(index=False))

    return df


# ============================================================
# 6. PRINT RESULTS
# ============================================================

def print_result(result):

    print("\n" + "=" * 55)

    print(result["method"])

    print("=" * 55)

    print("Processed bits:", result["processed_bits"])

    print("Unprocessed bits:", result["remaining_bits"])

    print("Total blocks:", result["total_blocks"])

    print("Corrected blocks:", result["corrected_blocks"])

    print("Successful blocks:", result["successful_blocks"])

    print("Failed blocks:", result["failed_blocks"])

    print("Disclosed bits:", result["disclosed_bits"])

    if "zero_error_blocks" in result:

        print("\nError distribution before correction:")

        print(
            "Blocks with 0 errors:",
            result["zero_error_blocks"]
        )

        print(
            "Blocks with 1 error:",
            result["one_error_blocks"]
        )

        if result["method"] == "Hamming (7,4)":

            print(
                "Blocks with 2 or more errors:",
                result["multiple_error_blocks"]
            )

        elif result["method"] == "BCH (15,7)":

            print(
                "Blocks with exactly 2 errors:",
                result["two_error_blocks"]
            )

            print(
                "Blocks with more than 2 errors:",
                result["more_than_two_blocks"]
            )

            print(
                "Uncorrectable syndromes:",
                result["uncorrectable_syndromes"]
            )

    if "code_rate" in result:

        print("\nLDPC configuration:")

        print("Code rate:", result["code_rate"])

        print("Shortened bits:", result["shortened_bits"])

        print("Punctured bits:", result["punctured_bits"])

        print(
            "Input bits per block:",
            result["input_bits_per_block"]
        )

        print(
            "Additional disclosed bits:",
            result["additional_disclosed_bits"]
        )

        print(
            "Communication rounds:",
            result["communication_rounds"]
        )

    print("\nEfficiency:", result["efficiency"])

    print(
        "Execution time:",
        result["execution_time"],
        "seconds"
    )

    print("Key agreement:", result["key_agreement"])

    # BCH failure diagnostics
    if result["method"] == "BCH (15,7)":

        print("\n========== BCH FAILURE DIAGNOSTICS ==========")

        if len(result["failed_block_details"]) == 0:

            print("No failed BCH blocks.")

        for detail in result["failed_block_details"]:

            print("\nBlock:", detail["block_index"])

            print(
                "Actual error weight:",
                detail["actual_error_weight"]
            )

            print(
                "Actual error positions:",
                detail["actual_error_positions"]
            )

            print(
                "Error syndrome:",
                detail["error_syndrome"]
            )

            print(
                "Estimated error positions:",
                detail["estimated_error_positions"]
            )

            print(
                "Remaining error positions:",
                detail["remaining_error_positions"]
            )


# ============================================================
# 7. MAIN COMPARISON
# ============================================================

def main():

    np.random.seed(42)

    CHANNEL_QBER = 0.02

    TOTAL_TRANSMISSIONS = 30000

    SAMPLE_SIZE = 1000

    print("\n========== BB84 SIMULATION ==========")

    alice_key, bob_key, qber_est = bb84_simulation(
        N=TOTAL_TRANSMISSIONS,
        channel_qber=CHANNEL_QBER,
        sample_size=SAMPLE_SIZE
    )

    print("Channel QBER:", CHANNEL_QBER)

    print("Estimated QBER:", qber_est)

    print("Alice key length:", len(alice_key))

    print("Bob key length:", len(bob_key))

    initial_errors = int(
        np.sum(alice_key != bob_key)
    )

    print("Errors before reconciliation:", initial_errors)

    # Load LDPC codes
    print("\nLoading LDPC codes...")

    codes = codes_from_file("codes_1944.txt")

    print("LDPC codes loaded successfully.")

    # Run all three methods on the same input keys
    print("\n========== RUNNING RECONCILIATION ==========")

    hamming_result = hamming_reconciliation(
        alice_key, bob_key, qber_est
    )

    bch_result = bch_reconciliation(
        alice_key, bob_key, qber_est
    )

    ldpc_result = ldpc_reconciliation_full(
        alice_key, bob_key, qber_est, codes
    )

    # Print individual results
    print_result(hamming_result)

    print_result(bch_result)

    print_result(ldpc_result)

    # Final comparison
    results = [
        hamming_result,
        bch_result,
        ldpc_result
    ]
    save_block_diagnostics(results)
    print("\n" + "=" * 105)

    print("FINAL COMPARISON: HAMMING vs BCH vs LDPC")

    print("=" * 105)

    print(
        f"{'Method':<18}"
        f"{'Processed':>12}"
        f"{'Blocks':>10}"
        f"{'Failed':>10}"
        f"{'Disclosed':>13}"
        f"{'Efficiency':>13}"
        f"{'Time (s)':>12}"
        f"{'Agreement':>12}"
    )

    print("-" * 105)

    for result in results:

        print(
            f"{result['method']:<18}"
            f"{result['processed_bits']:>12}"
            f"{result['total_blocks']:>10}"
            f"{result['failed_blocks']:>10}"
            f"{result['disclosed_bits']:>13}"
            f"{result['efficiency']:>13.4f}"
            f"{result['execution_time']:>12.5f}"
            f"{str(result['key_agreement']):>12}"
        )

    print("=" * 105)

    print("\n========== FINAL OBSERVATIONS ==========")

    for result in results:

        print(
            result["method"],
            "->",
            "Key agreement achieved"
            if result["key_agreement"]
            else "Key agreement NOT achieved"
        )

    print("\nInitial BB84 key errors:", initial_errors)

    print(
        "\nNote: Agreement is checked only on processed complete blocks."
    )

    print(
        "Unprocessed tail bits are not included in the agreement check."
    )

    print(
        "This is a simplified simulation, not a security-certified QKD implementation."
    )


def test_bch_correction_capability():

    print("\n========== BCH EXHAUSTIVE VALIDATION ==========")

    alice_block = np.array(
        [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0],
        dtype=np.uint8
    )

    total_tests = 0
    successful_tests = 0
    failed_tests = 0

    # Test every error pattern of weight 0, 1 and 2
    for error_weight in range(3):

        import itertools

        for positions in itertools.combinations(
            range(BCH_N), error_weight
        ):

            error_pattern = np.zeros(
                BCH_N, dtype=np.uint8
            )

            for position in positions:
                error_pattern[position] = 1

            bob_block = alice_block ^ error_pattern

            alice_value = block_to_integer(alice_block)
            bob_value = block_to_integer(bob_block)

            alice_syn = polynomial_remainder(
                alice_value, BCH_GENERATOR
            )

            bob_syn = polynomial_remainder(
                bob_value, BCH_GENERATOR
            )

            error_syn = alice_syn ^ bob_syn

            if error_syn in BCH_SYNDROME_TABLE:

                estimated_error = integer_to_error_pattern(
                    BCH_SYNDROME_TABLE[error_syn],
                    BCH_N
                )

                corrected_bob = bob_block ^ estimated_error

            else:

                corrected_bob = bob_block.copy()

            total_tests += 1

            if np.array_equal(alice_block, corrected_bob):
                successful_tests += 1
            else:
                failed_tests += 1

    print("Total tests:", total_tests)
    print("Successful tests:", successful_tests)
    print("Failed tests:", failed_tests)

    print(
        "BCH validation:",
        "PASSED" if failed_tests == 0 else "FAILED"
    )

# ============================================================
# 8. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    test_bch_correction_capability()
    main()
