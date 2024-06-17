import base64
import json
import os
from io import BytesIO

import gradio as gr
import websocket
from PIL import Image

api_key = os.environ.get('OPENAI_API_KEY')


class OpenDevinSession:
    def __init__(
        self,
        model='gpt-4o',
        agent='WorldModelAgent',
        language='en',
        api_key=api_key,
        port=3000,
    ):
        self.model = model
        self.agent = agent
        self.language = language
        self.api_key = api_key
        self.port = port
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

    def _reset(self, agent_state=None):
        self.token, self.status = None, None
        self.ws, self.agent_state = None, agent_state
        self.is_paused = False
        self.raw_messages = []
        self.browser_history = []
        self.action_messages = []

    def _close(self):
        print(f'Closing connection {self.token}')
        if self.ws:
            self.ws.close()
        self._reset()

    def __del__(self):
        self._close()


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
        yield (
            chat_history,
            screenshot,
            url,
            action_messages,
            browser_history,
            session,
            status,
            clear,
        )
    else:
        clear = gr.Button('Clear', interactive=False)
        if session.agent_state not in ['init', 'running', 'pausing', 'resuming']:
            session.agent = agent_selection
            print('API Key:', api_key)
            session.api_key = api_key if len(api_key) > 0 else 'test'
            action_messages = []
            browser_history = browser_history[:1]
            for agent_state in session.initialize(as_generator=True):
                status = get_status(agent_state)
                screenshot, url = browser_history[-1]
                yield (
                    chat_history,
                    screenshot,
                    url,
                    action_messages,
                    browser_history,
                    session,
                    status,
                    clear,
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
            yield (
                chat_history,
                screenshot,
                url,
                action_messages,
                browser_history,
                session,
                status,
                clear,
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
    default_agent = 'DummyWebAgent'

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

        action_messages = gr.State([])
        browser_history = gr.State([(blank, start_url)])
        session = gr.State(OpenDevinSession(agent=default_agent, port=default_port))
        # session = gr.State(OpenDevinSession(agent='WorldModelAgent', port=3000))
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
            ],
            queue=False,
        )

    demo.queue()
    demo.launch(share=False)
