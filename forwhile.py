import ast
import os

class LoopRefactor(ast.NodeTransformer):
    def __init__(self):
        self.while_id_map = {}        # Maps while iterators to their bounds
        self.while_nested_dict = {}   # Maps bounds to while loop bodies
        self.for_id_map = {}          # Maps for iterators to their bounds
        self.for_nested_dict = {}     # Maps bounds to for loop bodies
        self.init_statements = {}     # Maps loop indices to initialization statements
        self.loop_indices = []        # Tracks indices of converted for loops

    def collect_loops(self, tree):
        """Collect information about while and for loops within functions."""
        self.while_id_map = {}
        self.while_nested_dict = {}
        self.for_id_map = {}
        self.for_nested_dict = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.While) and isinstance(node.test, ast.Compare):
                # Extract while loop body, excluding AugAssign
                while_body = []
                constant_iterator = None
                for elem in node.body:
                    if not isinstance(elem, ast.AugAssign):
                        while_body.append(elem)
                    else:
                        constant_iterator = elem.value
                # Extract iterator and bound
                if (isinstance(node.test.left, ast.Name) and 
                    len(node.test.comparators) == 1 and 
                    isinstance(node.test.comparators[0], ast.Call) and 
                    isinstance(node.test.comparators[0].args[0], ast.Name)):
                    while_iterator = node.test.left.id
                    while_bound = node.test.comparators[0].args[0].id  # Assumes len(x)
                    self.while_id_map[while_iterator] = while_bound
                    self.while_nested_dict[while_bound] = while_body
            elif isinstance(node, ast.For):
                # Extract for loop details
                if (isinstance(node.target, ast.Name) and 
                    isinstance(node.iter, ast.Call) and 
                    len(node.iter.args) > 1 and 
                    isinstance(node.iter.args[1], ast.Call) and 
                    isinstance(node.iter.args[1].args[0], ast.Name)):
                    for_iterator = node.target.id
                    for_bound = node.iter.args[1].args[0].id  # Assumes range(0, len(x))
                    self.for_id_map[for_iterator] = for_bound
                    self.for_nested_dict[for_bound] = node.body

    def visit_FunctionDef(self, node):
        """Modify FunctionDef nodes to convert while and for loops."""
        self.collect_loops(node)
        new_body = node.body.copy()
        self.loop_indices = []
        self.init_statements = {}
        
        for idx, node_elem in enumerate(new_body):
            if (isinstance(node_elem, ast.While) and 
                isinstance(node_elem.test, ast.Compare) and 
                isinstance(node_elem.test.left, ast.Name) and 
                node_elem.test.left.id in self.while_id_map):
                # Convert while to for
                new_body[idx] = ast.For(
                    target=ast.Name(id=node_elem.test.left.id, ctx=ast.Store()),
                    iter=ast.Call(
                        func=ast.Name(id='range', ctx=ast.Load()),
                        args=[
                            ast.Constant(value=0),
                            ast.Name(id=self.while_id_map[node_elem.test.left.id], ctx=ast.Load())
                        ],
                        keywords=[]
                    ),
                    body=self.while_nested_dict[self.while_id_map[node_elem.test.left.id]],
                    orelse=[]
                )
                ast.fix_missing_locations(new_body[idx])
            elif isinstance(node_elem, ast.For):
                if (isinstance(node_elem.target, ast.Name) and 
                    node_elem.target.id in self.for_id_map):
                    self.loop_indices.append(idx)
                    iterator = node_elem.target.id
                    bound = self.for_id_map[iterator]
                    # Create initialization statement
                    self.init_statements[idx] = ast.Assign(
                        targets=[ast.Name(id=iterator, ctx=ast.Store())],
                        value=ast.Constant(value=0)
                    )
                    # Add increment to loop body
                    new_for_body = self.for_nested_dict[bound].copy()
                    new_for_body.append(
                        ast.AugAssign(
                            target=ast.Name(id=iterator, ctx=ast.Store()),
                            op=ast.Add(),
                            value=ast.Constant(value=1)
                        )
                    )
                    # Convert for to while
                    new_body[idx] = ast.While(
                        test=ast.Compare(
                            left=ast.Name(id=iterator, ctx=ast.Load()),
                            ops=[ast.Lt()],
                            comparators=[ast.Name(id=bound, ctx=ast.Load())]
                        ),
                        body=new_for_body,
                        orelse=[]
                    )
                    ast.fix_missing_locations(new_body[idx])
        
        # Insert initialization statements for converted while loops
        for init_idx in sorted(self.loop_indices, reverse=True):
            new_body.insert(init_idx, self.init_statements[init_idx])
            ast.fix_missing_locations(new_body[init_idx])
        
        node.body = new_body
        self.generic_visit(node)
        return node

    def refactor_loops(self, tree):
        """Process the AST to refactor loops and return modified code."""
        self.visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def get_modified_code(self, source_code):
        """Parse source code, refactor loops, and return modified code."""
        try:
            tree = ast.parse(source_code)
            return self.refactor_loops(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")

