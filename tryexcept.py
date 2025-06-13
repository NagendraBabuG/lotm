import ast
import os
import random

class ErrorHandlerRefactor(ast.NodeTransformer):
    SIGNATURES = ['pkcs1_15', 'pss', 'eddsa', 'DSS']
    EXCEPTIONS = ['e', 'exception', 'exc', 'err', 'error']
    ERROR_MESSAGES = ['ERROR:', 'Exception encountered.', 'Operation failed.']

    def __init__(self):
        self.def_mapping = {}      # Maps FunctionDef nodes to indices of lines to remove
        self.remove_lines = set()  # Set of indices of module-level lines to remove
        self.init_body = None      # Temporary storage for multi-statement try blocks

    def get_handler_block(self):
        """Generate an ExceptHandler block with a random exception name and message."""
        exception_id = random.choice(self.EXCEPTIONS)
        return [ast.ExceptHandler(
            type=ast.Name(id='Exception', ctx=ast.Load()),
            name=exception_id,
            body=[
                ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id='print', ctx=ast.Load()),
                        args=[
                            ast.JoinedStr(
                                values=[
                                    ast.Constant(value=random.choice(self.ERROR_MESSAGES)),
                                    ast.FormattedValue(
                                        value=ast.Name(id=exception_id, ctx=ast.Load()),
                                        conversion=-1
                                    )
                                ]
                            )
                        ],
                        keywords=[]
                    )
                )
            ]
        )]

    def process_assign(self, stmt, is_module_level=False):
        """Process an Assign node to determine if it needs a try-except block."""
        if not (isinstance(stmt, ast.Assign) and not isinstance(stmt.value, ast.Constant)):
            return None, False

        init_body = None
        needs_removal = False

        # Case 1: Signature generation via Call (e.g., pkcs1_15.new())
        if (isinstance(stmt.value, ast.Call) and 
            isinstance(stmt.value.func, ast.Attribute) and 
            isinstance(stmt.value.func.value, ast.Call) and 
            isinstance(stmt.value.func.value.func, ast.Attribute) and 
            isinstance(stmt.value.func.value.func.value, ast.Name) and 
            stmt.value.func.value.func.value.id in self.SIGNATURES):
            init_body = [stmt]

        # Case 2: Signer/verifier definition or signature generation/verification
        elif (isinstance(stmt.value, ast.Call) and 
              isinstance(stmt.value.func, ast.Attribute)):
            # Signer/verifier definition (e.g., pkcs1_15.new())
            if (isinstance(stmt.value.func.value, ast.Name) and 
                stmt.value.func.value.id in self.SIGNATURES):
                self.init_body = [stmt] if self.init_body is None else self.init_body + [stmt]
                return None, True  # Defer processing until sign/verify
            # Signature generation/verification (e.g., signer.sign())
            elif stmt.value.func.attr in ['sign', 'verify']:
                if self.init_body is not None:
                    init_body = self.init_body + [stmt]
                    self.init_body = None
                    needs_removal = True
                else:
                    init_body = [stmt]

        return init_body, needs_removal

    def visit_FunctionDef(self, node):
        """Modify FunctionDef nodes to add try-except blocks and mark lines for removal."""
        self.init_body = None
        new_body = node.body.copy()
        lines_to_remove = []

        for idx, stmt in enumerate(new_body):
            init_body, needs_removal = self.process_assign(stmt)
            if init_body:
                new_body[idx] = ast.Try(
                    body=init_body,
                    handlers=self.get_handler_block(),
                    orelse=[],
                    finalbody=[]
                )
                ast.fix_missing_locations(new_body[idx])
                if needs_removal and idx > 0:
                    lines_to_remove.append(idx - 1)

        # Remove redundant lines
        for remove_idx in sorted(lines_to_remove, reverse=True):
            new_body.pop(remove_idx)

        node.body = new_body
        self.generic_visit(node)
        return node

    def visit_Module(self, node):
        """Modify Module nodes to add try-except blocks and mark lines for removal."""
        self.init_body = None
        new_body = node.body.copy()
        self.remove_lines = set()

        for idx, stmt in enumerate(new_body):
            init_body, needs_removal = self.process_assign(stmt, is_module_level=True)
            if init_body:
                new_body[idx] = ast.Try(
                    body=init_body,
                    handlers=self.get_handler_block(),
                    orelse=[],
                    finalbody=[]
                )
                ast.fix_missing_locations(new_body[idx])
                if needs_removal and idx > 0:
                    self.remove_lines.add(idx - 1)

        # Remove redundant lines
        new_body = [stmt for idx, stmt in enumerate(new_body) if idx not in self.remove_lines]
        node.body = new_body
        self.generic_visit(node)
        return node

    def refactor_error_handling(self, tree):
        """Process the AST to add try-except blocks and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refacctored_code(self, source_code):
        """Parse source code, add try-except blocks, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.refactor_error_handling(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
