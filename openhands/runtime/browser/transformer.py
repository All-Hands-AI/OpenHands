import ast

import astor

from openhands.events.observation import BrowserOutputObservation


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


def rename_argument(new_name):
    def transformer(arg_node):
        # Change the name of the argument
        return [ast.keyword(arg=new_name, value=arg_node.value)]

    return transformer


def translate_computer_use_action_to_browsergym_action(
    code: str, last_obs: BrowserOutputObservation | None
) -> str:
    last_mouse_position = last_obs.mouse_position if last_obs else None
    if last_mouse_position is None or len(last_mouse_position) != 2:
        last_mouse_position = [0, 0]

    mapping = {
        'type': {
            'target_func': 'keyboard_type',
            'arg_transform': {'text': rename_argument('key')},
        },
        'key': {
            'target_func': 'keyboard_press',
            'arg_transform': {'text': rename_argument('key')},
        },
        'mouse_move': {
            'target_func': 'mouse_move',
            'arg_transform': {'coordinate': coordinate_split},
            'extra_args': [
                {
                    'name': 'from_x',
                    'value': last_mouse_position[0],
                },
                {
                    'name': 'from_y',
                    'value': last_mouse_position[1],
                },
            ],
        },
        'left_click_drag': {
            'target_func': 'mouse_drag_and_drop',
            'arg_transform': {'coordinate': coordinate_split},
            'extra_args': [
                {
                    'name': 'from_x',
                    'value': last_mouse_position[0],
                },
                {
                    'name': 'from_y',
                    'value': last_mouse_position[1],
                },
            ],
        },
        'left_click': {
            'target_func': 'mouse_click',
            'extra_args': [
                {'name': 'button', 'value': 'left'},
                {'name': 'x', 'value': last_mouse_position[0]},
                {'name': 'y', 'value': last_mouse_position[1]},
            ],
        },
        'right_click': {
            'target_func': 'mouse_click',
            'extra_args': [
                {'name': 'button', 'value': 'right'},
                {'name': 'x', 'value': last_mouse_position[0]},
                {'name': 'y', 'value': last_mouse_position[1]},
            ],
        },
        'middle_click': {
            'target_func': 'mouse_click',
            'extra_args': [
                {'name': 'button', 'value': 'middle'},
                {'name': 'x', 'value': last_mouse_position[0]},
                {'name': 'y', 'value': last_mouse_position[1]},
            ],
        },
        'double_click': {
            'target_func': 'mouse_dblclick',
            'extra_args': [
                {'name': 'button', 'value': 'left'},
                {'name': 'x', 'value': last_mouse_position[0]},
                {'name': 'y', 'value': last_mouse_position[1]},
            ],
        },
        'screenshot': {
            'target_func': 'noop',
        },
        'cursor_position': {
            'target_func': 'noop',
        },
    }

    # Parse code to AST, transform, and generate new code
    tree = ast.parse(code)
    transformer = ActionTransformer(mapping)
    transformed_tree = transformer.visit(tree)
    transformed_code = astor.to_source(transformed_tree)

    return transformed_code
