def sum_numbers_while(n):
    total = 0
    i = 1
    while i <= n:
        total += i
        i += 1
    return total

# Test
print(sum_numbers_while(5))  # Output: 15 (1+2+3+4+5)