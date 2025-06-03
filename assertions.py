import ast
import os

class AddAssertions(ast.NodeTransformer):
    def __init__(self):
        self.arg_list = []  # List to store function parameters
        self.comp_stmt = []  # List to store comparison statements (param != None)

    def collect_parameters(self, tree):
        """Collect all function parameters from the AST."""
        self.arg_list = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.args.args:  # Check if function has parameters
                    for argument in node.args.args:
                        self.arg_list.append(argument.arg)

    def create_comparison_statements(self):
        """Create comparison statements (param != None) for each parameter."""
        self.comp_stmt = []
        for arg in self.arg_list:
            stmt = ast.Compare(
                left=ast.Name(id=arg, ctx=ast.Load()),
                ops=[ast.NotEq()],
                comparators=[ast.Constant(value=None)]
            )
            self.comp_stmt.append(stmt)

    def visit_FunctionDef(self, node):
        """Modify FunctionDef nodes to insert assertions for non-None parameters."""
        # Collect parameters specific to this function
        func_args = [arg.arg for arg in node.args.args]
        if not func_args:
            return node  # No parameters, no assertions needed

        # Create comparison statements for this function's parameters
        comp_stmt = [
            ast.Compare(
                left=ast.Name(id=arg, ctx=ast.Load()),
                ops=[ast.NotEq()],
                comparators=[ast.Constant(value=None)]
            )
            for arg in func_args
        ]

        # Create an assertion with a BoolOp (AND) combining all comparisons
        if comp_stmt:
            assert_stmt = ast.Assert(
                test=ast.BoolOp(
                    op=ast.And(),
                    values=comp_stmt
                )
            )
            # Insert assertion at the beginning of the function body
            node.body.insert(0, assert_stmt)

        # Continue processing child nodes
        self.generic_visit(node)
        return node

    def add_assertions(self, tree):
        """Process the AST to add assertions and return the modified code."""
        # Collect parameters and create comparison statements
        self.collect_parameters(tree)
        self.create_comparison_statements()

        # Transform the AST to insert assertions
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        """Parse source code, add assertions, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.add_assertions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")


