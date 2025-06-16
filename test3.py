def find_first_even_while(lst):
    index = 0
    while index < len(lst):
        if lst[index] % 2 == 0:
            return lst[index]
        index += 1
    return None  # Return None if no even number is found

# Test
print(find_first_even_while([1, 3, 4, 6, 7]))  # Output: 4