import ast
import os

class AddDefaultArgValue(ast.NodeTransformer):
    def __init__(self):
        self.func_par_map = {}  # Maps function names to parameter lists
        self.par_con_map = {}   # Maps parameter names to constant values
        self.con_par_map = {}   # Maps constant values to parameter names
        self.var_idx = 0        # Counter for generating unique parameter names

    def collect_mappings(self, tree):
        """Collect constant arguments and keywords from function calls."""
        self.func_par_map = {}
        self.par_con_map = {}
        self.var_idx = 0
        used_params = set()  # Track used parameter names to avoid duplicates

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                current_list = []
                for node2 in node.body:
                    if isinstance(node2, ast.Assign) and isinstance(node2.value, ast.Call):
                        # Handle positional arguments
                        if node2.value.args:
                            for arg in node2.value.args:
                                if isinstance(arg, ast.Constant):
                                    while True:
                                        var_name = f"var{self.var_idx}"
                                        self.var_idx += 1
                                        if var_name not in used_params:
                                            break
                                    self.par_con_map[var_name] = arg.value
                                    current_list.append(var_name)
                                    used_params.add(var_name)
                        # Handle keyword arguments
                        if node2.value.keywords:
                            for kw in node2.value.keywords:
                                if isinstance(kw.value, ast.Constant) and kw.arg not in used_params:
                                    self.par_con_map[kw.arg] = kw.value.value
                                    current_list.append(kw.arg)
                                    used_params.add(kw.arg)
                if current_list:
                    self.func_par_map[node.name] = current_list

    def print_mappings(self):
        """Print mappings for debugging."""
        print(f"Function-Parameter Mapping:\n{self.func_par_map}")
        print(f"Parameter-Constant Mapping:\n{self.par_con_map}")

    def visit_FunctionDef(self, node):
        """Modify FunctionDef nodes to add parameters with default constants."""
        if node.name in self.func_par_map:
            new_args = node.args.args.copy()
            new_defaults = node.args.defaults.copy()
            for parameter in self.func_par_map[node.name]:
                if parameter:
                    new_args.append(ast.arg(arg=parameter))
                    new_defaults.append(ast.Constant(value=self.par_con_map[parameter]))
                    self.con_par_map[self.par_con_map[parameter]] = parameter
            node.args = ast.arguments(
                posonlyargs=node.args.posonlyargs,
                args=new_args,
                vararg=node.args.vararg,
                kwonlyargs=node.args.kwonlyargs,
                kw_defaults=node.args.kw_defaults,
                kwarg=node.args.kwarg,
                defaults=new_defaults
            )
            ast.fix_missing_locations(node)
        return self.generic_visit(node)

    def visit_Call(self, node):
        """Replace constant arguments and keywords with parameter references."""
        new_args = node.args.copy()
        new_keywords = node.keywords.copy()
        # Replace positional arguments
        for arg in node.args:
            if isinstance(arg, ast.Constant) and arg.value in self.con_par_map:
                new_args.remove(arg)
                new_args.append(ast.Name(id=self.con_par_map[arg.value], ctx=ast.Load()))
        # Replace keyword arguments
        for kw in node.keywords:
            if isinstance(kw.value, ast.Constant) and kw.value.value in self.con_par_map:
                new_args.append(ast.Name(id=self.con_par_map[kw.value.value], ctx=ast.Load()))
                new_keywords.remove(kw)
        node.args = new_args
        node.keywords = new_keywords
        ast.fix_missing_locations(node)
        return node

    def refactor_functions(self, tree):
        self.collect_mappings(tree)
        self.con_par_map = {}  # Reset before second pass
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            self.print_mappings()
            return self.refactor_functions(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")
