
import numpy as np

H = np.array([
    [1, 0, 1, 0, 1, 0, 1],
    [0, 1, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1]
], dtype=int)


def calculate_syndrome(bits):
    bits = np.asarray(bits, dtype=int)
    return (H @ bits) % 2


def reconcile_block(alice_bits, bob_bits):
    alice_bits = np.asarray(alice_bits, dtype=int)
    bob_bits = np.asarray(bob_bits, dtype=int)

    if len(alice_bits) != 7 or len(bob_bits) != 7:
        raise ValueError("Both blocks must contain 7 bits.")

    # Alice publicly sends her syndrome
    syndrome_alice = calculate_syndrome(alice_bits)

    # Bob calculates his syndrome
    syndrome_bob = calculate_syndrome(bob_bits)

    # Difference gives the error syndrome
    error_syndrome = (syndrome_alice + syndrome_bob) % 2

    # Identify error position
    error_position = 0

    for i in range(7):
        if np.array_equal(error_syndrome, H[:, i]):
            error_position = i
            break

    # Correct Bob's bit if a single error is identified
    corrected = bob_bits.copy()

    if error_position != 0:
        corrected[error_position] ^= 1

    return corrected, error_syndrome, error_position
