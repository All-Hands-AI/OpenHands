import base64
import json
import os
from io import BytesIO

import gradio as gr
import networkx as nx
import plotly.graph_objects as go
import websocket
from PIL import Image

api_key = os.environ.get('OPENAI_API_KEY')
LINE_LEN = 18


class Node:
    def __init__(self, state, in_action, state_info, status, reward, parent):
        self.state = state
        self.in_action = in_action
        self.state_info = state_info
        self.status = status
        self.parent = parent
        self.children = []
        self.reward = reward
        self.Q = 0.0
        self.uct = 0.0


class OpenDevinSession:
    def __init__(
        self,
        agent,
        port,
        model,
        language='en',
        api_key=api_key,
    ):
        self.model = model
        self.agent = agent
        self.language = language
        self.api_key = api_key
        self.port = port

        self.figure = None

        self._reset()

    def initialize(self, as_generator=False):
        self.agent_state = None
        if self.ws:
            self._close()
        self.ws = websocket.WebSocket()
        self.ws.connect(f'ws://127.0.0.1:{self.port}/ws')

        payload = {
            'action': 'initialize',
            'args': {
                'LLM_MODEL': self.model,
                'AGENT': self.agent,
                'LANGUAGE': self.language,
                'LLM_API_KEY': self.api_key,
            },
        }
        self.ws.send(json.dumps(payload))

        while self.agent_state != 'init':
            message = self._get_message()
            if message.get('token'):
                self.token, self.status = message['token'], message['status']
            elif message.get('observation') == 'agent_state_changed':
                self.agent_state = message['extras']['agent_state']
                if as_generator:
                    yield self.agent_state
        print(f'{self.agent} Initialized')

    def pause(self):
        if self.agent_state != 'running':
            raise ValueError('Agent not running, nothing to pause')
        print('Pausing')

        payload = {'action': 'change_agent_state', 'args': {'agent_state': 'paused'}}
        self.ws.send(json.dumps(payload))

        self.agent_state = 'pausing'

    def resume(self):
        if self.agent_state != 'paused':
            raise ValueError('Agent not paused, nothing to resume')
        print('Resuming')

        payload = {'action': 'change_agent_state', 'args': {'agent_state': 'running'}}
        self.ws.send(json.dumps(payload))

        self.agent_state = 'resuming'

    def run(self, task):
        if self.agent_state not in ['init', 'running', 'pausing', 'resuming', 'paused']:
            raise ValueError(
                'Agent not initialized. Please run the initialize() method first'
            )

        if task is not None:
            payload = {'action': 'message', 'args': {'content': task}}
            self.ws.send(json.dumps(payload))

        while self.agent_state not in ['finished', 'paused']:
            message = self._get_message()
            self._read_message(message)

            self._update_figure(message)

            print(self.agent_state)
            yield message

    def _get_message(self):
        # try:
        message = json.loads(self.ws.recv())
        self.raw_messages.append(message)
        # print(list(message.keys()))
        return message
        # except json.decoder.JSONDecodeError as e:
        #     return {}

    def _read_message(self, message, verbose=True):
        if message.get('token'):
            self.token = message['token']
            self.status = message['status']
            printable = message
        elif message.get('observation') == 'agent_state_changed':
            self.agent_state = message['extras']['agent_state']
            printable = message
        elif 'action' in message:
            self.action_messages.append(message['message'])
            printable = message
        elif 'extras' in message and 'screenshot' in message['extras']:
            image_data = base64.b64decode(message['extras']['screenshot'])
            screenshot = Image.open(BytesIO(image_data))
            url = message['extras']['url']
            printable = {
                k: v for k, v in message.items() if k not in ['extras', 'content']
            }
            self.browser_history.append((screenshot, url))

        if verbose:
            print(printable)

    def _update_figure(self, message):
        if (
            ('args' in message)
            and ('thought' in message['args'])
            and (message['args']['thought'].find('MCTS') != -1)
        ):
            log_content = message['args']['thought']
            self.figure = parse_and_visualize(log_content)

    def _reset(self, agent_state=None):
        self.token, self.status = None, None
        self.ws, self.agent_state = None, agent_state
        self.is_paused = False
        self.raw_messages = []
        self.browser_history = []
        self.action_messages = []
        self.figure = go.Figure()

    def _close(self):
        print(f'Closing connection {self.token}')
        if self.ws:
            self.ws.close()
        self._reset()

    def __del__(self):
        self._close()


def process_string(string, line_len):
    word_list = string.split(' ')
    if len(word_list) <= line_len:
        return string
    else:
        lines = []
        for i in range(0, len(word_list), line_len):
            lines.append(' '.join(word_list[i : i + line_len]))
        return '<br>'.join(lines)


def update_Q(node):
    if len(node.children) == 0:
        node.Q = node.reward
        return node.reward
    else:
        total_Q = node.reward
        for child in node.children:
            if child.status != 'Init' and child.status != 'null':
                total_Q += update_Q(child)
        node.Q = total_Q
        return node.Q


def parse_log(log_file):
    count = 0
    nodes = {}
    current_node = None
    root = None
    chosen_node = -1
    in_next_state = False
    next_state = ''
    in_state = False
    state_info = ''

    # with open(log_file) as f:
    log_string = log_file
    lines = log_string.strip().split('\n')
    # graphs = []
    # nodes_list = []

    for line in lines:
        if line.startswith('*State*'):
            in_state = True
            state_info = (
                state_info + process_string(line.split(': ')[1], LINE_LEN) + '<br>'
            )

        if (
            in_state
            and not (line.startswith('*State*'))
            and not (line.startswith('*Replan Reasoning*'))
        ):
            state_info = state_info + process_string(line, LINE_LEN) + '<br>'

        if line.startswith('*Replan Reasoning*'):
            in_state = False
            current_node = Node(count, 'null', state_info, 'Init', 0.0, None)
            if root is None:
                root = current_node
            nodes[count] = current_node
            count += 1
            state_info = ''

        if line.startswith('*Strategy Candidate*'):
            strat_info = process_string(line.split(': ')[1], LINE_LEN)

        if line.startswith('*Fast Reward*'):
            reward = float(line.split(': ')[1])
            nodes[count] = Node(count, strat_info, 'null', 'null', reward, None)
            current_node.children.append(nodes[count])
            nodes[count].parent = current_node
            count += 1

        if line.startswith('*Expanded Strategy*'):
            expanded_strat = process_string(line.split(': ')[1], LINE_LEN)
            for node_num, node in nodes.items():
                if node.in_action == expanded_strat:
                    chosen_node = node_num

        if line.startswith('*Next State*'):
            in_next_state = True
            next_state = (
                next_state + process_string(line.split(': ')[1], LINE_LEN) + '<br>'
            )

        if (
            in_next_state
            and not (line.startswith('*Next State*'))
            and not (line.startswith('*Status*'))
        ):
            next_state = next_state + process_string(line, LINE_LEN) + '<br>'

        if line.startswith('*Status*'):
            status = process_string(line.split(': ')[1], LINE_LEN)
            nodes[chosen_node].state_info = next_state
            nodes[chosen_node].status = status
            current_node = nodes[chosen_node]
            chosen_node = -1
            in_next_state = False
            next_state = ''

        # if line.startswith("BROWSER_ACTIONS: "):
        #     update_Q(root)
        #     graphs.append(root)
        #     nodes_list.append(nodes)
        #     count = 0
        #     nodes = {}
        #     root = None
        #     current_node = None
    update_Q(root)
    # return graphs, nodes_list
    return root, nodes


def visualize_tree_plotly(root, nodes):
    G = nx.DiGraph()

    def add_edges(node):
        for child in node.children:
            G.add_edge(node.state, child.state)
            add_edges(child)

    def get_nodes_by_level(node, level, level_nodes):
        if level not in level_nodes:
            level_nodes[level] = []
        level_nodes[level].append(node)
        for child in node.children:
            get_nodes_by_level(child, level + 1, level_nodes)

    add_edges(root)

    level_nodes = {}
    get_nodes_by_level(root, 0, level_nodes)

    highest_q_nodes = set()
    for level, nodes_at_level in level_nodes.items():
        highest_q_node = max(nodes_at_level, key=lambda x: x.Q)
        highest_q_nodes.add(highest_q_node.state)

    pos = hierarchy_pos(G, root.state)
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=2, color='black'),
        hoverinfo='none',
        mode='lines',
        showlegend=False,
    )

    node_x = []
    node_y = []
    labels = []
    hover_texts = []
    colors = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        hover_text = (
            f'<b>State {node}</b><br>'
            f'<b>Reward:</b> {nodes[node].reward}<br>'
            f'<b>Q:</b> {nodes[node].Q}<br>'
            f'<b>In Action:</b> {nodes[node].in_action}<br>'
            f'<b>State Info:</b> {nodes[node].state_info}<br>'
            f'<b>Status:</b> {nodes[node].status}'
        )
        hover_texts.append(hover_text)
        labels.append(str(node))
        if node in highest_q_nodes:
            colors.append('pink')
        else:
            colors.append('#FFD700')

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hoverinfo='text',
        text=hover_texts,
        hoverlabel=dict(font=dict(size=16)),
        marker=dict(showscale=False, color=colors, size=40, line_width=4),
        showlegend=False,
    )

    label_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='text',
        text=labels,
        textposition='middle center',
        hoverinfo='none',
        textfont=dict(family='Arial', size=16, color='black', weight='bold'),
        showlegend=False,
    )

    agent_choice_trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            size=10,
            color='pink',
            line=dict(width=2),
        ),
        showlegend=True,
        name='Agent Choice',
    )

    candidate_trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            size=10,
            color='#FFD700',
            line=dict(width=2),
        ),
        showlegend=True,
        name='Candidate',
    )

    fig = go.Figure(
        data=[edge_trace, node_trace, label_trace, agent_choice_trace, candidate_trace],
        layout=go.Layout(
            title='Tree visualization of log file',
            titlefont_size=16,
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(text='', showarrow=False, xref='paper', yref='paper')],
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
        ),
    )

    return fig


def hierarchy_pos(G, root, width=1.0, vert_gap=0.1, vert_loc=0, xcenter=0.5):
    pos = _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)
    return pos


def _hierarchy_pos(
    G,
    root,
    width=1.0,
    vert_gap=0.1,
    vert_loc=0,
    xcenter=0.5,
    pos=None,
    parent=None,
    parsed=None,
):
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    if parsed is None:
        parsed = []

    pos[root] = (xcenter, vert_loc)
    children = list(G.neighbors(root))
    if not isinstance(G, nx.DiGraph) and parent is not None:
        children.remove(parent)
    if len(children) != 0:
        dx = width / len(children)
        nextx = xcenter - width / 2 - dx / 2
        for child in children:
            nextx += dx
            pos = _hierarchy_pos(
                G,
                child,
                width=dx,
                vert_gap=vert_gap,
                vert_loc=vert_loc - vert_gap,
                xcenter=nextx,
                pos=pos,
                parent=root,
                parsed=parsed,
            )
    return pos


def parse_and_visualize(log_file):
    root, nodes = parse_log(log_file)
    fig = visualize_tree_plotly(root, nodes)
    return fig


def user(user_message, history):
    return '', history + [[user_message, None]]


def get_status(agent_state):
    if agent_state == 'loading':
        status = 'Agent Status: 🟡 Loading'
    elif agent_state == 'init':
        status = 'Agent Status: 🟢 Initialized'
    elif agent_state == 'running':
        status = 'Agent Status: 🟢 Running'
    elif agent_state == 'pausing':
        status = 'Agent Status: 🟢 Pausing'
    elif agent_state == 'paused':
        status = 'Agent Status: 🟡 Paused'
    elif agent_state == 'resuming':
        status = 'Agent Status: 🟡 Resuming'
    elif agent_state == 'finished':
        status = 'Agent Status: 🟢 Finished'
    elif agent_state == 'stopped':
        status = 'Agent Status: 🔴 Stopped'
    elif agent_state is None:
        status = 'Agent Status: 🔴 Inactive'
    else:
        status = f'Agent Status: 🔴 {agent_state}'

    return status


def get_messages(
    chat_history,
    action_messages,
    browser_history,
    session,
    status,
    agent_selection,
    model_selection,
    api_key,
):
    print('Get Messages', session.agent_state)
    if len(chat_history) > 0:
        if chat_history[-1][1] is None:
            user_message = chat_history[-1][0]
            chat_history[-1][1] = ''
        else:
            user_message = None
            chat_history[-1][1] = chat_history[-1][1].strip() + '\n\n'
    else:
        user_message = None

    if (
        session.agent_state is None or session.agent_state in ['paused', 'finished']
    ) and user_message is None:
        clear = gr.Button('Clear', interactive=True)
        if len(chat_history) > 0:
            chat_history[-1][1] = '\n\n'.join(action_messages)
        status = get_status(session.agent_state)
        screenshot, url = browser_history[-1]

        if session.figure:
            figure = session.figure
        else:
            figure = go.Figure()

        yield (
            chat_history,
            screenshot,
            url,
            action_messages,
            browser_history,
            session,
            status,
            clear,
            figure,
        )
    else:
        clear = gr.Button('Clear', interactive=False)
        if session.agent_state not in ['init', 'running', 'pausing', 'resuming']:
            session.agent = agent_selection
            # session.model = model_port_config[model_selection]["provider"] + '/' + model_selection
            session.model = model_selection
            print('API Key:', api_key)
            session.api_key = api_key if len(api_key) > 0 else 'test'
            action_messages = []
            browser_history = browser_history[:1]
            for agent_state in session.initialize(as_generator=True):
                status = get_status(agent_state)
                screenshot, url = browser_history[-1]

                if session.figure:
                    figure = session.figure
                else:
                    figure = go.Figure()

                yield (
                    chat_history,
                    screenshot,
                    url,
                    action_messages,
                    browser_history,
                    session,
                    status,
                    clear,
                    figure,
                )

        for message in session.run(user_message):
            clear = gr.Button('Clear', interactive=(session.agent_state == 'finished'))
            status = get_status(session.agent_state)
            while len(session.action_messages) > len(action_messages):
                diff = len(session.action_messages) - len(action_messages)
                action_messages.append(session.action_messages[-diff])
                # chat_history[-1][1] += session.action_messages[-diff] + '\n\n'
                chat_history[-1][1] = '\n\n'.join(action_messages)
            while len(session.browser_history) > (len(browser_history) - 1):
                diff = len(session.browser_history) - (len(browser_history) - 1)
                browser_history.append(session.browser_history[-diff])
            screenshot, url = browser_history[-1]

            if session.figure:
                figure = session.figure
            else:
                figure = go.Figure()

            yield (
                chat_history,
                screenshot,
                url,
                action_messages,
                browser_history,
                session,
                status,
                clear,
                figure,
            )


def clear_page(browser_history, session):
    browser_history = browser_history[:1]
    current_screenshot, current_url = browser_history[-1]
    session._close()
    status = get_status(session.agent_state)
    # pause_resume = gr.Button("Pause", interactive=False)
    return (
        None,
        'Pause',
        False,
        current_screenshot,
        current_url,
        [],
        browser_history,
        session,
        status,
        go.Figure(),
    )


def pause_resume_task(is_paused, session, status):
    if not is_paused and session.agent_state == 'running':
        session.pause()
        is_paused = True
    elif is_paused and session.agent_state == 'paused':
        session.resume()
        is_paused = False

    button = 'Resume' if is_paused else 'Pause'
    status = get_status(session.agent_state)
    return button, is_paused, session, status


if __name__ == '__main__':
    default_port = 3000
    with open('Makefile') as f:
        while True:
            line = f.readline()
            if 'BACKEND_PORT' in line:
                default_port = int(line.split('=')[1].strip())
                break
            if not line:
                break
    default_agent = 'WorldModelAgent'

    model_port_config = {}
    with open('model_port_config.json') as f:
        model_port_config = json.load(f)
    model_list = list(model_port_config.keys())
    default_model = model_list[0]

    with gr.Blocks() as demo:
        title = gr.Markdown('# FastAgent')
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                with gr.Group():
                    agent_selection = gr.Dropdown(
                        ['DummyWebAgent', 'WorldModelAgent'],
                        value=default_agent,
                        interactive=True,
                        label='Agent',
                        info='Choose your own adventure partner!',
                    )
                    model_selection = gr.Dropdown(
                        model_list,
                        value=default_model,
                        interactive=True,
                        label='Model',
                        info='Choose the model you would like to use',
                    )
                    api_key = gr.Textbox(label='API Key', placeholder='Your API Key')
                    chatbot = gr.Chatbot()
                with gr.Group():
                    with gr.Row():
                        msg = gr.Textbox(container=False, show_label=False, scale=7)
                        submit = gr.Button(
                            'Submit',
                            variant='primary',
                            scale=1,
                            min_width=150,
                        )
                        submit_triggers = [msg.submit, submit.click]
                with gr.Row():
                    pause_resume = gr.Button('Pause')
                    clear = gr.Button('Clear')

                status = gr.Markdown('Agent Status: 🔴 Inactive')

            with gr.Column(scale=2):
                with gr.Group():
                    start_url = 'about:blank'
                    url = gr.Textbox(
                        start_url, label='URL', interactive=False, max_lines=1
                    )
                    blank = Image.new('RGB', (1280, 720), (255, 255, 255))
                    screenshot = gr.Image(blank, interactive=False, label='Webpage')
                    plot = gr.Plot(go.Figure(), label='Agent Planning Process')

        action_messages = gr.State([])
        browser_history = gr.State([(blank, start_url)])
        session = gr.State(
            OpenDevinSession(
                agent=default_agent, port=default_port, model=default_model
            )
        )
        is_paused = gr.State(False)
        # chat_msg = msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False)
        chat_msg = gr.events.on(
            submit_triggers, user, [msg, chatbot], [msg, chatbot], queue=False
        )
        bot_msg = chat_msg.then(
            get_messages,
            [
                chatbot,
                action_messages,
                browser_history,
                session,
                status,
                agent_selection,
                model_selection,
                api_key,
            ],
            [
                chatbot,
                screenshot,
                url,
                action_messages,
                browser_history,
                session,
                status,
                clear,
                plot,
            ],
        )
        (
            pause_resume.click(
                pause_resume_task,
                [is_paused, session, status],
                [pause_resume, is_paused, session, status],
                queue=False,
            ).then(
                get_messages,
                [
                    chatbot,
                    action_messages,
                    browser_history,
                    session,
                    status,
                    agent_selection,
                    model_selection,
                    api_key,
                ],
                [
                    chatbot,
                    screenshot,
                    url,
                    action_messages,
                    browser_history,
                    session,
                    status,
                    clear,
                    plot,
                ],
            )
        )
        clear.click(
            clear_page,
            [browser_history, session],
            [
                chatbot,
                pause_resume,
                is_paused,
                screenshot,
                url,
                action_messages,
                browser_history,
                session,
                status,
                plot,
            ],
            queue=False,
        )

    demo.queue()
    demo.launch(share=True)
