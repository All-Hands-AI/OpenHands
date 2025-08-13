import math


def total_byte_entropy_stats(python_code):
    # Count the occurrence of each byte (character for simplicity)
    byte_counts = {}
    for byte in python_code.encode('utf-8'):
        byte_counts[byte] = byte_counts.get(byte, 0) + 1

    total_bytes = sum(byte_counts.values())
    entropy = -sum(
        (count / total_bytes) * math.log2(count / total_bytes)
        for count in byte_counts.values()
    )

    return {'total_byte_entropy': entropy}


def average_nulls_stats(tree, num_lines):
    total_nulls = 0
    nulls_per_line = {}  # Dictionary to count nulls per line

    def traverse(node):
        nonlocal total_nulls
        if node.type == 'null_literal':
            total_nulls += 1
            line_number = node.start_point[0]  # Get line number
            if line_number in nulls_per_line:
                nulls_per_line[line_number] += 1
            else:
                nulls_per_line[line_number] = 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)

    # Calculate average nulls per line
    avg_nulls = total_nulls / num_lines if num_lines > 0 else 0

    # Calculate max nulls on any line
    max_nulls_on_any_line = max(nulls_per_line.values()) if nulls_per_line else 0

    return {
        'avg_nulls': avg_nulls,
        'total_nulls': total_nulls,
        'max_nulls': max_nulls_on_any_line,
        'has_nulls': 1 if total_nulls > 0 else 0,
    }


def arithmetic_operations_stats(tree, num_lines):
    # Dictionary to hold counts of each arithmetic operation
    op_counts = {'+': 0, '-': 0, '*': 0, '/': 0, '%': 0}
    total_ops = 0

    # Function to traverse the AST and update operation counts
    def traverse(node):
        nonlocal total_ops
        if node.type == 'binary_expression' or node.type == 'update_expression':
            for child in node.children:
                if child.type == 'operator':
                    op = child.text.decode('utf8')
                    if op in op_counts:
                        op_counts[op] += 1
                        total_ops += 1
        else:
            for child in node.children:
                traverse(child)

    traverse(tree.root_node)

    return {
        'total_arithmetic_operations': total_ops,
        'avg_arithmetic_operations': total_ops / num_lines,
    }


def numbers_floats_stats(tree, num_lines):
    total_numbers = 0
    total_floats = 0

    def traverse(node):
        nonlocal total_numbers, total_floats
        if node.type in ['integer_literal', 'decimal_literal']:
            total_numbers += 1
            if (
                '.' in node.text.decode('utf8')
                or 'e' in node.text.decode('utf8').lower()
            ):
                total_floats += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return {'total_numbers': total_numbers, 'total_floats': total_floats}


def code_stats(python_code):
    lines = python_code.strip().split('\n')
    total_line_length = sum(len(line) for line in lines)
    max_line_length = max(len(line) for line in lines)
    return {
        'total_line_length': total_line_length,
        'max_line_length': max_line_length,
        'avg_characters': total_line_length / len(lines),
    }


def assertions_stats(tree, num_lines):
    total_assertions = 0

    def traverse(node):
        nonlocal total_assertions
        if node.type == 'assert_statement':
            total_assertions += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return {
        'total_assertions': total_assertions,
        'total_has_assertions': 1 if total_assertions > 0 else 0,
    }


def class_instances_stats(tree, num_lines):
    total_class_instances = 0

    def traverse(node):
        nonlocal total_class_instances
        if node.type == 'object_creation_expression':
            total_class_instances += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return {'total_class_instances': total_class_instances}


def has_execeptions(tree, num_lines):
    total_has_exceptions = 0

    def traverse(node):
        nonlocal total_has_exceptions
        if node.type == 'try_statement':
            total_has_exceptions += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    return {'total_has_exceptions': 1 if total_has_exceptions > 0 else 0}


def distinct_methods_stats(tree, num_lines):
    method_names = set()
    total_nodes = 0

    def traverse(node):
        nonlocal total_nodes
        if node.type == 'method_declaration':
            for child in node.children:
                if child.type == 'identifier':
                    method_names.add(child.text.decode('utf8'))
                    break
        total_nodes += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    total_distinct_methods = len(method_names)
    total_method_ratio = (
        total_distinct_methods / (total_nodes - total_distinct_methods)
        if total_nodes > total_distinct_methods
        else 0
    )

    return {
        'total_distinct_methods': total_distinct_methods,
        'total_method_ratio': total_method_ratio,
    }


def loops_stats(tree, num_lines):
    """Calculate the average number of loops."""
    total_loops = 0

    def traverse(node):
        nonlocal total_loops
        if node.type in ['for_statement', 'while_statement', 'do_statement']:
            total_loops += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    avg_loops = total_loops / num_lines
    return {'avg_loops': avg_loops}


def branches_stats(tree, num_lines):
    """Calculate the average number of branches (conditional statements)."""
    total_branches = 0

    def traverse(node):
        nonlocal total_branches
        if node.type in ['if_statement', 'switch_statement']:
            total_branches += 1
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)
    # Assuming each branch is its own, this might need refinement based on definition
    avg_branches = total_branches / num_lines
    return {'avg_branches': avg_branches}


def string_stats(tree, num_lines):
    string_literals = []

    # Function to traverse the AST and collect string literals
    def traverse(node):
        if node.type == 'string_literal':
            # Extracting the string literal, excluding the quotation marks
            literal_text = node.text.decode('utf8')[1:-1]
            string_literals.append(literal_text)
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)

    # Calculate the average string length
    total_length = sum(len(s) for s in string_literals)
    avg_length = total_length / num_lines
    return {'avg_str_length': avg_length}


def identifier_stats(tree, num_lines):
    root_node = tree.root_node
    identifier_counts = {}  # Dictionary to count occurrences of each identifier
    total_nodes = 0  # Counter for all nodes

    # Function to recursively count identifiers and all nodes, gathering their stats
    def count(node):
        nonlocal identifier_counts, total_nodes
        iden_count = 0
        max_length = 0
        total_nodes += 1  # Increment total nodes for every node visited
        if node.type == 'identifier':
            identifier = node.text.decode('utf8')  # Assuming UTF-8 encoding
            iden_count += 1
            identifier_counts[identifier] = identifier_counts.get(identifier, 0) + 1
            iden_length = len(identifier)
            if iden_length > max_length:
                max_length = iden_length
        for child in node.children:
            child_count, child_max_length = count(child)
            iden_count += child_count
            if child_max_length > max_length:
                max_length = child_max_length
        return iden_count, max_length

    total_identifiers, max_identifier_length = count(root_node)
    total_unique_identifiers = len(identifier_counts)
    total_identifier_length = sum(len(k) * v for k, v in identifier_counts.items())
    avg_identifier_length = total_identifier_length / num_lines

    # Calculate the identifier ratio as total identifiers over total nodes
    identifier_ratio = total_identifiers / total_nodes if total_nodes > 0 else 0

    return {
        'total_identifiers': total_identifiers,
        'total_identifier_length': total_identifier_length,
        'max_identifier_length': max_identifier_length,
        'avg_identifier_length': avg_identifier_length,
        'total_unique_identifiers': total_unique_identifiers,
        'total_identifier_ratio': identifier_ratio,  # Include the new ratio in the returned dictionary
        'total_nodes': total_nodes,  # Include total node count for reference or further calculations
    }


def compute_regression(results):
    components = {
        'total_line_length': -0.0001,
        'max_line_length': -0.0021,
        'total_identifiers': 0.0076,
        'total_identifier_length': -0.0004,
        'max_identifier_length': -0.0067,
        'avg_identifier_length': -0.005,
        'avg_arithmetic_operations': 0.0225,
        'avg_branches': 0.9886,
        'avg_loops': 0.1572,
        'total_assertions': 0.0119,
        'total_has_assertions': -0.0147,
        'avg_characters': 0.1242,
        'total_class_instances': -0.043,
        'total_distinct_methods': -0.0127,
        'avg_str_length': 0.0026,
        'total_has_exceptions': 0.1206,
        'total_unique_identifiers': -0.019,
        'max_nulls': -0.0712,
        'total_numbers': -0.0078,
        'avg_nulls': 0.1444,
        'total_identifier_ratio': 0.334,
        'total_method_ratio': 0.0406,
        'total_floats': -0.0174,
        'total_byte_entropy': -0.3917,
    }
    test_score = 0

    for component in components:
        test_score += components[component] * results[component]

    test_score += 5.7501
    return test_score


def compute_readability(python_code):
    # Create parser and set up language
    import tree_sitter_python
    from tree_sitter import Language, Parser

    parser = Parser(Language(tree_sitter_python.language()))

    results = code_stats(python_code)

    num_lines = len(python_code.strip().split('\n'))
    results.update(total_byte_entropy_stats(python_code))

    tree = parser.parse(bytes(python_code, 'utf8'))

    results.update(identifier_stats(tree, num_lines))
    results.update(loops_stats(tree, num_lines))
    results.update(branches_stats(tree, num_lines))
    results.update(distinct_methods_stats(tree, num_lines))
    results.update(has_execeptions(tree, num_lines))
    results.update(class_instances_stats(tree, num_lines))
    results.update(assertions_stats(tree, num_lines))
    results.update(numbers_floats_stats(tree, num_lines))
    results.update(average_nulls_stats(tree, num_lines))
    results.update(arithmetic_operations_stats(tree, num_lines))
    results.update(string_stats(tree, num_lines))

    score = compute_regression(results)
    return score
