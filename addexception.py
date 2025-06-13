import ast
import os
import random

class TryExceptRefactor(ast.NodeTransformer):
    ERROR_MESSAGES = ['ERROR: ', "Exception encountered: ", "Operation Failed: "]
    EXCEPTION_POOL = ['e', 'exception', 'exc', 'err', 'error']

    def get_handler_block(self, exc_id):
        """Generate an ExceptHandler block with the given exception name."""
        return [
            ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                name=exc_id,
                body=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id='print', ctx=ast.Load()),
                            args=[
                                ast.JoinedStr(
                                    values=[
                                        ast.Constant(value=random.choice(self.ERROR_MESSAGES)),
                                        ast.FormattedValue(
                                            value=ast.Name(id=exc_id, ctx=ast.Load()),
                                            conversion=-1
                                        )
                                    ]
                                )
                            ],
                            keywords=[]
                        )
                    )
                ]
            )
        ]

    def visit_FunctionDef(self, node):
        """Modify FunctionDef nodes to wrap their body in a try-except block."""
        if not node.body:  # Skip empty functions
            return node

        # Create a copy of the body
        init_body = [elem for elem in node.body]
        
        # Generate try-except block with a random exception name
        exc_id = random.choice(self.EXCEPTION_POOL)
        new_body = [
            ast.Try(
                body=init_body,
                handlers=self.get_handler_block(exc_id),
                orelse=[],
                finalbody=[]
            )
        ]
        
        # Update the function body
        node.body = new_body
        ast.fix_missing_locations(node)
        self.generic_visit(node)
        return node
           
    def refactor_try_except(self, tree):           
        """Process the AST to add try-except blocks and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):                                                       
        """Parse source code, add try-except blocks, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.refactor_try_except(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
