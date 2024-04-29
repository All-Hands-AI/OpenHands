from flask import Flask, request, jsonify
import gymnasium as gym

from utils import image_to_jpg_base64_url

app = Flask(__name__)

env = gym.make(
    'browsergym/openended',
    start_url='about:blank',
    wait_for_user_message=False,
    headless=True,
    disable_env_checker=True,
)
obs, info = env.reset()

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    return jsonify({'status': 'alive'})

@app.route('/step', methods=['POST'])
def step():
    action_data = request.json
    action = action_data['action']
    obs, reward, terminated, truncated, info = env.step(action)
    # make observation serializable
    obs['screenshot'] = image_to_jpg_base64_url(obs['screenshot'])
    obs['active_page_index'] = int(obs['active_page_index'])
    obs['elapsed_time'] = float(obs['elapsed_time'])
    return jsonify(obs)

@app.route('/teardown', methods=['POST'])
def teardown():
    try:
        env.close()
        return jsonify({'error': False})
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=5000, threaded=False) # must be single threaded to ensure playwright browser singleton
