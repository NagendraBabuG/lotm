def sum_numbers_for(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

# Test
print(sum_numbers_for(5))  # Output: 15 (1+2+3+4+5)