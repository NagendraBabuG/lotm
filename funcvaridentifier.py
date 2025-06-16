import ast
import os
import random

class FuncVarNameRefactator:
    def __init__(self):
        # Predefined data structures
        self.code_identifiers = [
            "key", "public_key", "signature", "b64_signature", "verifier", "decoded_message"
        ]
        self.identifiers = {
            'keygen': ["key_generator", "keygen_function", "generate_keys"],
            'sign': ['signing_function', 'sign_function', 'sign_generation', 'signer'],
            'verify': ['verifying_function', 'verify_function', 'sign_verification', "verifier"],
            'key': ['api_key', 'signing_key', 'pri_key', 'private_key', 'key'],
            'public_key': ['public_api_key', 'verifying_key', 'pub_key', 'public_key'],
            'message': ['data', 'payload', 'plaintext', 'message'],
            'signature': ['signed_data', 'signed', 'digital_signature', 'signature'],
            'b64_signature': ["b64_signature", "sigb64", "signed_b64", "b64_result", "b64_data", "final_b64"],
            'verifier': ["validator", "verify_object", "ver_obj"],
            'decoded_message': ["decoded", "signed_message", "dec_msg"]
        }
        self.algorithms = {'signatures': ["pkcs1_v1_5", "pss", "DSS", "eddsa"]}
        self.key_types = ['DSA', 'RSA', 'ECC']
        self.key_sizes = [256, 512, 1024, 2048, 4096]
        self.ecc_key_sizes = ['p192', 'p224', 'p256', 'p384', 'p521']
        self.old_names = {}  # Maps old identifiers to new ones
        self.func_perm = {}  # Maps function names to parameter permutations

    def mutate_code(self, source_code):
        """Mutate source code by renaming identifiers and shuffling parameters."""
        if isinstance(source_code, bytes):
            source_code = source_code.decode("utf-8")
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")

        self.old_names = {}
        self.func_perm = {}

        # First pass: Mutate function definitions and assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Rename function
                old_func_name = node.name
                node.name = random.choice(self.identifiers.get(old_func_name, [old_func_name]))
                self.old_names[old_func_name] = node.name

                # Mutate and shuffle parameters
                par_values = [arg.arg for arg in node.args.args]
                for arg in node.args.args:
                    if arg.arg not in self.identifiers:
                        new_name = random.choice(self.identifiers.get(arg.arg, [arg.arg]))
                        if arg.arg not in self.old_names:
                            self.old_names[arg.arg] = new_name
                        arg.arg = new_name

                # Shuffle parameters
                if par_values:
                    shuffled_params = par_values.copy()
                    random.shuffle(shuffled_params)
                    temp = []
                    for arg in node.args.args:
                        new_param = shuffled_params.pop(0)
                        arg.arg = new_param
                        temp.append(new_param)
                    self.func_perm[node.name] = temp

            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                # Mutate assignment targets
                if (isinstance(node.value.func, ast.Attribute) and 
                    len(node.targets) > 0 and 
                    isinstance(node.targets[0], ast.Name) and 
                    node.targets[0].id in self.code_identifiers and 
                    node.targets[0].id not in self.old_names):
                    method_choice = random.choice(self.identifiers.get(node.targets[0].id, [node.targets[0].id]))
                    self.old_names[node.targets[0].id] = method_choice
                    node.targets[0].id = method_choice

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                # Mutate cryptographic method calls
                if node.func.attr == "new":
                    node.args = [arg for arg in node.args if not (
                        isinstance(arg, ast.Constant) and 
                        arg.value in ["fips-186-3", "rfc8032"]
                    )]
                    method_choice = random.choice(self.algorithms['signatures'])
                    node.func.value.id = method_choice
                    if method_choice == "DSS":
                        node.args.append(ast.Constant(value="fips-186-3"))
                    elif method_choice == "eddsa":
                        node.args.append(ast.Constant(value="rfc8032"))
                elif node.func.attr == "generate":
                    node.func.value.id = random.choice(self.key_types)
                    for kw in node.keywords:
                        if node.func.value.id == "ECC":
                            kw.arg = "curve"
                            kw.value = ast.Constant(value=random.choice(self.ecc_key_sizes))
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            arg.value = random.choice(self.ecc_key_sizes if node.func.value.id == "ECC" else self.key_sizes)

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in self.old_names:
                node.id = self.old_names[node.id]

        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Name) and 
                node.func.id in self.func_perm):
                new_args = []
                for idx, param in enumerate(self.func_perm[node.func.id]):
                    if idx < len(node.args):
                        new_args.append(node.args[idx])
                    else:
                        new_args.append(ast.Name(id=param, ctx=ast.Load()))
                node.args = new_args

        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def crossover_code(self, code1, code2):
        split1 = code1.split("\n")
        split2 = code2.split("\n")
        crossover_point = random.randint(1, min(len(split1), len(split2)) - 1)
        return "\n".join(split1[:crossover_point] + split2[crossover_point:])

    def generate_variants(self, initial_code, generations=2, population_size=2):
        """Generate multiple code variants through mutation."""
        population = [initial_code]
        final_population = []

        for _ in range(generations):
            mutated_code = self.mutate_code(initial_code)
            final_population.append(mutated_code)

            new_population = []
            while len(new_population) < population_size:
                parent_code = random.choice(population)
                mutated_code = self.mutate_code(parent_code)
                new_population.append(mutated_code)

            population = new_population

        return final_population

    def get_refactored_code(self, source_code):
        try:
            tree = ast.parse(source_code)
            return self.generate_variants(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source code: {e}")