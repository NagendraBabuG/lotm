import ast
import os
from random import shuffle

class ShuffleFunctions(ast.NodeTransformer):
    def __init__(self):
        self.function_nodes = []  # List to store FunctionDef nodes
        self.line_list = []      # List to store positions of functions in module body

    def collect_functions(self, tree):
        """Collect FunctionDef nodes and their positions in the module body."""
        self.function_nodes = []
        self.line_list = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                for idx, node2 in enumerate(node.body):
                    if isinstance(node2, ast.FunctionDef):
                        self.function_nodes.append(node2)
                        self.line_list.append(idx)
                break  # Exit after processing the Module node

    def shuffle_functions(self):
        """Shuffle the order of collected function nodes."""
        shuffle(self.function_nodes)

    def visit_Module(self, node):
        """Modify the Module node to reorder FunctionDef nodes."""
        if not self.function_nodes:
            return node  # No functions to shuffle

        # Create a new body with the shuffled function order
        new_body = node.body.copy()  # Copy to avoid modifying during iteration
        inner_idx = 0
        for fnode in self.function_nodes:
            new_body[self.line_list[inner_idx]] = fnode
            inner_idx += 1
        node.body = new_body

        # Continue processing child nodes
        self.generic_visit(node)
        return node

    def reorder_functions(self, tree):
        """Process the AST to shuffle functions and return the modified code."""
        # Collect functions and their positions
        self.collect_functions(tree)
        # Shuffle the function nodes
        self.shuffle_functions()
        # Apply the transformation
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        """Parse source code, shuffle functions, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.reorder_functions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
