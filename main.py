# main.py
import os
from assertions import AddAssertions
from function_reorder import ShuffleFunctions
from ifelse import TernaryRefactor
from partials import KeywordArgRefactor
from singline_lambda import LambdaRefactor


def process_files(dir_path):
    add_assert = AddAssertions()
    shuffle_funcs = ShuffleFunctions()
    ifelse_ternary = TernaryRefactor()
    partials = KeywordArgRefactor()
    lambda_refact = LambdaRefactor()
    
    for filename in os.listdir(dir_path):
        if filename.endswith(".py"):
            file_path = os.path.join(dir_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()


            #refactored_code = add_assert.get_refactored_code(source_code)
            #refactored_code = shuffle_funcs.get_refactored_code(source_code)
            #refactored_code = ifelse_ternary.get_refactored_code(source_code)
            #refactored_code = partials.get_refactored_code(source_code)
            refactored_code = lambda_refact.get_refactored_code(source_code)
            print(f"\n****** Final Code for {filename} ******\n")
            print(refactored_code)

            res_file_path = os.path.join('./routput/', filename)
            with open(res_file_path, "w", encoding="utf-8") as f:
                f.write(refactored_code)

if __name__ == "__main__":
    process_files('./input/')
