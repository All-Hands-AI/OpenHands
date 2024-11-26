import ast

import astor


class ActionTransformer(ast.NodeTransformer):
    def __init__(self, mapping):
        self.mapping = mapping

    def visit_Call(self, node):
        # Check if the function name matches one in the mapping
        if isinstance(node.func, ast.Name) and node.func.id in self.mapping:
            transform_info = self.mapping[node.func.id]
            target_func = transform_info['target_func']
            arg_transform = transform_info.get('arg_transform')
            extra_args = transform_info.get('extra_args', [])

            # Update the function name
            node.func.id = target_func

            # Apply argument transformations if defined
            if arg_transform:
                new_keywords = []
                for kw in node.keywords:
                    if kw.arg in arg_transform:
                        new_keywords.extend(arg_transform[kw.arg](kw))
                    else:
                        new_keywords.append(kw)
                node.keywords = new_keywords

            # Add extra arguments
            for extra_arg in extra_args:
                node.keywords.append(
                    ast.keyword(
                        arg=extra_arg['name'],
                        value=ast.Constant(value=extra_arg['value']),
                    )
                )

        return self.generic_visit(node)


def coordinate_split(arg_node):
    if isinstance(arg_node.value, ast.Tuple) and len(arg_node.value.elts) == 2:
        x_arg = ast.keyword(arg='to_x', value=arg_node.value.elts[0])
        y_arg = ast.keyword(arg='to_y', value=arg_node.value.elts[1])
        return [x_arg, y_arg]
    return []


def translate_computer_use_action_to_browsergym_action(code: str) -> str:
    mapping = {
        'type': {
            'target_func': 'keyboard_type',
        },
        'key': {
            'target_func': 'keyboard_type',
        },
        'mouse_move': {
            'target_func': 'mouse_move',
            'arg_transform': {'coordinate': coordinate_split},
        },
        'left_click_drag': {
            'target_func': 'mouse_drag_and_drop',
            'arg_transform': {'coordinate': coordinate_split},
        },
        'left_click': {
            'target_func': 'mouse_click',
            'extra_args': [{'name': 'button', 'value': 'left'}],
        },
        'right_click': {
            'target_func': 'mouse_click',
            'extra_args': [{'name': 'button', 'value': 'right'}],
        },
        'middle_click': {
            'target_func': 'mouse_click',
            'extra_args': [{'name': 'button', 'value': 'middle'}],
        },
        'double_click': {
            'target_func': 'mouse_double_click',
            'extra_args': [{'name': 'button', 'value': 'left'}],
        },
        'screenshot': {
            'target_func': 'noop',
        },
        'cursor_position': 'noop',
    }

    # Parse code to AST, transform, and generate new code
    tree = ast.parse(code)
    transformer = ActionTransformer(mapping)
    transformed_tree = transformer.visit(tree)
    transformed_code = astor.to_source(transformed_tree)

    return transformed_code


if __name__ == '__main__':
    code = """result = type("Hello, World!")"""
    assert (
        translate_computer_use_action_to_browsergym_action(code)
        == "result = keyboard_type('Hello, World!')\n"
    )

    code = """result = mouse_move(coordinate=(100, 200))"""
    assert (
        translate_computer_use_action_to_browsergym_action(code)
        == 'result = mouse_move(to_x=100, to_y=200)\n'
    )

    code = """result = left_click()"""
    assert (
        translate_computer_use_action_to_browsergym_action(code)
        == "result = mouse_click(button='left')\n"
    )
