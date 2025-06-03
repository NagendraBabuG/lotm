import ast
import os

class TernaryRefactor(ast.NodeTransformer):
    def __init__(self):
        self.if_test_node = []        # Stores test nodes of if statements
        self.if_body_node = []       # Stores body nodes of if statements (non-Expr)
        self.if_or_else_node = []    # Stores orelse nodes of if statements (non-Expr)
        self.tern_test_node = []     # Stores test nodes of ternary if statements
        self.tern_body_node = []     # Stores body nodes of ternary if statements
        self.tern_or_else_node = []  # Stores orelse nodes of ternary if statements

    def collect_nodes(self, tree):
        """Collect relevant nodes from if and IfExp statements."""
        self.if_test_node = []
        self.if_body_node = []
        self.if_or_else_node = []
        self.tern_test_node = []
        self.tern_body_node = []
        self.tern_or_else_node = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                self.if_test_node.append(node.test)
                for stmt in node.body:
                    if not isinstance(stmt, ast.Expr):
                        self.if_body_node.append(stmt)
                for stmt in node.orelse:
                    if not isinstance(stmt, ast.Expr):
                        self.if_or_else_node.append(stmt)
            elif isinstance(node, ast.IfExp):
                self.tern_test_node.append(node.test)
                self.tern_body_node.append(node.body)
                self.tern_or_else_node.append(node.orelse)

    def check_for_assign(self, node):
        """Check if a node or its orelse contains assignment statements."""
        if isinstance(node, ast.If):
            for exp in node.body:
                if not isinstance(exp, ast.Expr):
                    return True
            if node.orelse:
                return self.check_for_assign(node.orelse[0])
        return False

    def nested_elif_generator(self, node):
        """Recursively convert if statements to ternary IfExp nodes."""
        if not isinstance(node, ast.If):
            return node.value
        return ast.IfExp(
            test=node.test,
            body=node.body[0].value,
            orelse=self.nested_elif_generator(node.orelse[0]) if node.orelse else ast.Constant(value=None)
        )

    def nested_ifexp_generator(self, node):
        """Recursively convert ternary IfExp nodes to if statements."""
        if not isinstance(node, ast.IfExp):
            return ast.Expr(value=node)
        return ast.If(
            test=node.test,
            body=[ast.Expr(value=node.body)],
            orelse=[self.nested_ifexp_generator(node.orelse)]
        )

    def visit_Module(self, node):
        """Modify the Module node to convert if and IfExp nodes."""
        # Collect nodes first
        self.collect_nodes(node)
        index = 0  # Index for if nodes
        tern_index = 0  # Index for ternary nodes
        new_body = node.body.copy()  # Copy to avoid modifying during iteration
        for idx, node2 in enumerate(new_body):
            if isinstance(node2, ast.If):
                # Convert if to ternary if no assignments are present
                if not self.check_for_assign(node2):
                    new_body[idx] = ast.Expr(
                        value=self.nested_elif_generator(node2)
                    )
                    index += 1
            elif isinstance(node2, ast.Expr) and isinstance(node2.value, ast.IfExp) and not isinstance(node2, ast.Assign):
                # Convert ternary to if
                new_body[idx] = ast.If(
                    test=self.tern_test_node[tern_index],
                    body=[ast.Expr(value=self.tern_body_node[tern_index])],
                    orelse=[self.nested_ifexp_generator(self.tern_or_else_node[tern_index])]
                )
                ast.fix_missing_locations(new_body[idx])
                tern_index += 1
        node.body = new_body
        self.generic_visit(node)
        return node

    def refactor_ternary(self, tree):
        """Process the AST to refactor if/ternary expressions and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        """Parse source code, refactor if/ternary expressions, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.refactor_ternary(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")

