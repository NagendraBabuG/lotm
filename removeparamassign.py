import ast
import os

class ParameterRenameRefactor(ast.NodeTransformer):
    def __init__(self):
        self.par_var_map = {}  # Maps original parameters to new variable names
        self.current_func = None  # Tracks current FunctionDef being processed

    def _repeated_check(self, node):
        """Rename parameter references in function call arguments."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Call):
                # Recursively process nested function calls
                node.func.value = self._repeated_check(node.func.value)
            # Update arguments
            new_args = []
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.par_var_map:
                    new_args.append(ast.Name(id=self.par_var_map[arg.id], ctx=arg.ctx))
                else:
                    new_args.append(arg)
            node.args = new_args
        elif isinstance(node.func, ast.Name):
            # Update arguments for direct function calls
            new_args = []
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.par_var_map:
                    new_args.append(ast.Name(id=self.par_var_map[arg.id], ctx=arg.ctx))
                else:
                    new_args.append(arg)
            node.args = new_args
        return node

    def visit_FunctionDef(self, node):
        """Process FunctionDef nodes to rename repeated parameters."""
        self.current_func = node.name
        self.par_var_map = {}
        par_list = [arg.arg for arg in node.args.args]  # Collect parameters
        var_idx = 0  # Counter for unique variable names
        new_body = node.body.copy()  # Copy body for safe modification

        # Update assignments
        for idx, node2 in enumerate(new_body):
            if isinstance(node2, ast.Assign):
                new_targets = []
                for target in node2.targets:
                    if isinstance(target, ast.Name) and target.id in par_list:
                        var_name = f"var{var_idx}"
                        var_idx += 1
                        self.par_var_map[target.id] = var_name
                        new_targets.append(ast.Name(id=var_name, ctx=target.ctx))
                    else:
                        new_targets.append(target)
                node2.targets = new_targets
                ast.fix_missing_locations(node2)

        # Update return statements and function calls
        for node2 in ast.walk(node):
            if isinstance(node2, ast.Return) and node2.value:
                if isinstance(node2.value, ast.Tuple):
                    new_elts = []
                    for obj in node2.value.elts:
                        if isinstance(obj, ast.Name) and obj.id in self.par_var_map:
                            new_elts.append(ast.Name(id=self.par_var_map[obj.id], ctx=obj.ctx))
                        else:
                            new_elts.append(obj)
                    node2.value.elts = new_elts
                elif isinstance(node2.value, ast.Name) and node2.value.id in self.par_var_map:
                    node2.value.id = self.par_var_map[node2.value.id]
                ast.fix_missing_locations(node2)
            elif isinstance(node2, ast.Call):
                node2 = self._repeated_check(node2)
                ast.fix_missing_locations(node2)

        node.body = new_body
        self.current_func = None
        return self.generic_visit(node)

    def refactor_parameters(self, tree):
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.refactor_parameters(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
