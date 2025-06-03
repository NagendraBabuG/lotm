import ast
import os

class LambdaRefactor(ast.NodeTransformer):
    def __init__(self):
        self.func_node_map = {}  # Mapping of function names to their return expressions
        self.func_args_map = {}  # Mapping of function names to their parameter lists
        self.func_lambda = []    # List of function names to track lambda conversions
        self.fdef = []           # List of FunctionDef nodes to remove

    def collect_functions(self, tree):
        """Collect single-return-statement functions and their details."""
        self.func_node_map = {}
        self.func_args_map = {}
        self.func_lambda = []
        self.fdef = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and len(node.body) == 1:
                if isinstance(node.body[0], ast.Return):
                    self.fdef.append(node)
                    self.func_node_map[node.name] = node.body[0].value
                    self.func_args_map[node.name] = [arg.arg for arg in node.args.args]
                    self.func_lambda.append(node.name)

    def print_extracted_expressions(self):
        """Print extracted return expressions for debugging."""
        print("******* EXTRACTED EXPRESSION *******")
        for node in self.func_node_map.values():
            print(ast.unparse(node))

    def visit_Module(self, node):
        """Modify the Module node to convert function calls to lambda assignments."""
        # Collect function information
        self.collect_functions(node)
        
        # Process module body
        new_body = node.body.copy()  # Copy to avoid modifying during iteration
        for idx, node2 in enumerate(new_body):
            if (isinstance(node2, ast.Assign) and 
                isinstance(node2.value, ast.Call) and 
                isinstance(node2.value.func, ast.Name) and 
                node2.value.func.id in self.func_lambda):
                func_name = node2.value.func.id
                self.func_lambda.remove(func_name)  # Mark function as processed
                
                # Create lambda assignment
                lambda_stmt = ast.Assign(
                    targets=node2.targets,  # Preserve original targets
                    value=ast.Lambda(
                        args=ast.arguments(
                            posonlyargs=[],
                            args=[
                                ast.arg(arg=param) 
                                for param in self.func_args_map[func_name]
                            ],
                            kwonlyargs=[],
                            kw_defaults=[],
                            kwarg=None,
                            defaults=[]
                        ),
                        body=self.func_node_map[func_name]
                    )
                )
                new_body[idx] = lambda_stmt
                ast.fix_missing_locations(new_body[idx])
        
        # Remove original function definitions
        new_body = [n for n in new_body if n not in self.fdef]
        node.body = new_body
        self.generic_visit(node)
        return node

    def refactor_lambda(self, tree):
        """Process the AST to refactor functions to lambdas and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        """Parse source code, refactor to lambdas, and return modified code."""
        try:
            tree = ast.parse(source_code)
            self.print_extracted_expressions()  # Print expressions for debugging
            return self.refactor_lambda(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
