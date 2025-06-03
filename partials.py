import ast
import os

class KeywordArgRefactor(ast.NodeTransformer):
    def __init__(self):
        self.var_con_map = {}  # Mapping of variables to their constant values
        self.remove_list = []  # List of assignment nodes to remove

    def collect_assignments(self, tree):
        """Collect constant assignments and mark them for removal."""
        self.var_con_map = {}
        self.remove_list = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):  # Ensure target is a variable
                        self.var_con_map[target.id] = node.value.value
                        self.remove_list.append(node)

    def print_mapping(self):
        """Print the variable-to-constant mapping for debugging."""
        print("Variable to Constant Mapping:", self.var_con_map)

    def visit_Module(self, node):
        """Modify the Module node to remove assignments and convert args to keywords."""
        # Collect assignments first
        self.collect_assignments(node)
        
        # Remove redundant assignments from the module body
        new_body = [n for n in node.body if n not in self.remove_list]
        
        # Process function calls to convert positional args to keyword args
        for idx, node2 in enumerate(new_body):
            if isinstance(node2, ast.Assign) and isinstance(node2.value, ast.Call) and node2.value.args:
                new_args = node2.value.args.copy()  # Copy to avoid modifying during iteration
                new_keywords = node2.value.keywords.copy()
                for arg in node2.value.args:
                    if isinstance(arg, ast.Name) and arg.id in self.var_con_map:
                        # Add keyword argument
                        new_keywords.append(
                            ast.keyword(
                                arg=arg.id,
                                value=ast.Constant(value=self.var_con_map[arg.id])
                            )
                        )
                        # Remove positional argument
                        new_args.remove(arg)
                        # Remove from mapping to mark as processed
                        self.var_con_map.pop(arg.id)
                # Update the call node
                node2.value.args = new_args
                node2.value.keywords = new_keywords
                ast.fix_missing_locations(node2.value)
        
        # Update the module body
        node.body = new_body
        self.generic_visit(node)
        return node

    def refactor_keywords(self, tree):
        """Process the AST to refactor arguments and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        """Parse source code, refactor arguments, and return modified code."""
        try:
            tree = ast.parse(source_code)
            self.print_mapping()  # Print mapping for debugging
            return self.refactor_keywords(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")

