# QKD Error Reconciliation: Hamming, BCH and LDPC Codes

## Overview

This project implements and compares three classical error-correction techniques — **Hamming Codes, BCH Codes, and Low-Density Parity-Check (LDPC) Codes** — for error reconciliation in Quantum Key Distribution (QKD).

The work focuses on the post-processing stage of the BB84 protocol, where Alice and Bob aim to reconcile their sifted keys in the presence of errors introduced by a noisy communication channel.

The objective is to study the error-correction capability, reconciliation efficiency, decoding performance, and computational runtime of different coding techniques under varying Quantum Bit Error Rates (QBER).

## Objectives

- Simulate the BB84 quantum key distribution protocol and generate sifted keys.
- Introduce bit-flip errors to model a noisy communication channel.
- Estimate the Quantum Bit Error Rate (QBER).
- Implement Hamming, BCH, and LDPC-based error reconciliation.
- Compare the algorithms based on decoding success, information leakage, failed blocks, and execution time.
- Analyse the performance of different codes at varying QBER values.

## Error-Correction Techniques

### 1. Hamming Code (7,4)

- Uses 7-bit codewords to encode 4 information bits.
- Minimum distance: 3.
- Corrects up to 1 bit error per block.
- Uses syndrome-based error detection and correction.

### 2. BCH Code (15,7)

- Uses a binary BCH code with a block length of 15 bits.
- Designed minimum distance: 5.
- Guaranteed correction capability: up to 2 errors per block.
- Implements syndrome-based decoding using a lookup table (LUT).

### 3. LDPC Code

- Uses Low-Density Parity-Check codes for error reconciliation.
- Employs iterative belief-propagation decoding.
- Uses parity-check information exchanged between Alice and Bob.
- Performance depends on the code construction, block length, and decoding parameters.

## Methodology

The project follows these general steps:

1. Generate random bit strings and measurement bases for Alice and Bob.
2. Perform basis reconciliation to obtain sifted keys.
3. Introduce bit-flip errors to simulate a noisy channel.
4. Estimate QBER using publicly revealed sample bits.
5. Apply Hamming, BCH, and LDPC error-reconciliation techniques.
6. Compare the corrected keys and evaluate decoding performance.
7. Analyse the results for different QBER values.

## Performance Evaluation

The algorithms are evaluated using the following metrics:

- **Decoding Success Rate:** Fraction of trials in which the reconciled keys match.
- **Failed Blocks:** Number of blocks that could not be successfully corrected.
- **Reconciliation Efficiency:** Ratio of disclosed information to the asymptotic information-theoretic benchmark.
- **Execution Time:** Computational time required for reconciliation.

The QBER values investigated are 1%, 2%, 3%, 5%, 8%, and 10%.

## Repository Structure

The repository is organised into folders containing the BB84 simulation, error-correction implementations, analysis scripts, and experimental results.

*See the folders in this repository for the corresponding source code, notebooks, and output files.*

## Technologies Used

- Python
- NumPy
- SciPy
- Matplotlib
- Pandas
- Jupyter Notebook
- Git and GitHub

## Limitations

- The communication channel is modelled using a simplified classical bit-flip error model.
- The implementation focuses on error reconciliation rather than a complete composable-security QKD system.
- Privacy amplification and finite-key security analysis are not implemented.
- Results depend on the selected code parameters and simulation trials.

## References

1. C. H. Bennett and G. Brassard, "Quantum cryptography: Public key distribution and coin tossing," IEEE International Conference on Computers, Systems and Signal Processing, 1984.
2. G. Brassard and L. Salvail, "Secret-key reconciliation by public discussion," EUROCRYPT '93, 1994.
3. R. W. Hamming, "Error detecting and error correcting codes," Bell System Technical Journal, 1950.
4. R. C. Bose and D. K. Ray-Chaudhuri, "On a class of error correcting binary group codes," Information and Control, 1960.
5. R. G. Gallager, "Low-density parity-check codes," IRE Transactions on Information Theory, 1962.
6. Heramb25, [Repetition-Code-LUT-complete-vs-compressed](https://github.com/Heramb25/Repetition-Code-LUT-complete-vs-compressed-) — Reference implementation studied for LUT-based decoding concepts.

---

**Author:** Deepanshu Ranolia  
**Institution:** Indian Institute of Technology Jodhpur  
**Project:** Specialization Project — Quantum Technologies