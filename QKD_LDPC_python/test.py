from hamming_qkd import reconcile_block

alice = [1, 0, 1, 1, 0, 1, 0]
bob   = [1, 0, 1, 1, 1, 1, 0]

corrected, syndrome, position = reconcile_block(alice, bob)

print("Alice's key:     ", alice)
print("Bob's key:       ", bob)
print("Error syndrome:  ", syndrome)
print("Error position:  ", position)
print("Corrected key:   ", corrected)
print("Successful:      ", list(alice) == list(corrected))