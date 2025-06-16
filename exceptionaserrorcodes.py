import ast
import os

class ExceptionRefactor(ast.NodeTransformer):
    def visit_Try(self, node):
        new_body = node.body.copy()
        new_handlers = [handler for handler in node.handlers]  # Copy handlers
        append_return = False  # Flag to append return 1 to try block
        remove_returns = False  # Flag to remove returns from try block

        for handler_idx, handler in enumerate(new_handlers):
            if isinstance(handler, ast.ExceptHandler):
                new_handler_body = handler.body.copy()
                for stmt_idx, stmt in enumerate(new_handler_body):
                    if isinstance(stmt, ast.Raise):
                        new_handler_body[stmt_idx] = ast.Return(
                            value=ast.Constant(value=0)
                        )
                        append_return = True
                        ast.fix_missing_locations(new_handler_body[stmt_idx])
                    elif isinstance(stmt, ast.Return):
                        new_handler_body[stmt_idx] = ast.Raise(
                            exc=ast.Call(
                                func=ast.Name(id='Exception', ctx=ast.Load()),
                                args=[ast.Constant(value='Operation failed')],
                                keywords=[]
                            )
                        )
                        remove_returns = True
                        ast.fix_missing_locations(new_handler_body[stmt_idx])
                new_handlers[handler_idx] = ast.ExceptHandler(
                    type=handler.type,
                    name=handler.name,
                    body=new_handler_body
                )
                ast.fix_missing_locations(new_handlers[handler_idx])

        if remove_returns:
            new_body = [stmt for stmt in new_body if not isinstance(stmt, ast.Return)]

        if append_return:
            new_body.append(ast.Return(value=ast.Constant(value=1)))
            ast.fix_missing_locations(new_body[-1])

        node.body = new_body
        node.handlers = new_handlers
        return self.generic_visit(node)

    def visit_If(self, node):
        new_body = node.body.copy()
        new_orelse = node.orelse.copy()

        for idx, stmt in enumerate(new_body):
            if isinstance(stmt, ast.Raise):
                new_body[idx] = ast.Return(value=ast.Constant(value=1))
                ast.fix_missing_locations(new_body[idx])
            elif (isinstance(stmt, ast.Return) and 
                  isinstance(stmt.value, ast.Constant) and 
                  isinstance(stmt.value.value, int)):
                new_body[idx] = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id='Exception', ctx=ast.Load()),
                        args=[ast.Constant(value='Operation failed')],
                        keywords=[]
                    )
                )
                ast.fix_missing_locations(new_body[idx])

        # Process else body
        for idx, stmt in enumerate(new_orelse):
            if isinstance(stmt, ast.Raise):
                new_orelse[idx] = ast.Return(value=ast.Constant(value=0))
                ast.fix_missing_locations(new_orelse[idx])
            elif (isinstance(stmt, ast.Return) and 
                  isinstance(stmt.value, ast.Constant) and 
                  isinstance(stmt.value.value, int)):
                new_orelse[idx] = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id='Exception', ctx=ast.Load()),
                        args=[ast.Constant(value='Operation failed')],
                        keywords=[]
                    )
                )
                ast.fix_missing_locations(new_orelse[idx])

        node.body = new_body
        node.orelse = new_orelse
        return self.generic_visit(node)

    def refactor_exceptions(self, tree):
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.refactor_exceptions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
