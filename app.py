import time

from flask import Flask, request
from scienceworld import ScienceWorldEnv


app = Flask('ScienceWorld')
context = {}


def get_env() -> ScienceWorldEnv:
    if 'env' not in context:
        context['env'] = ScienceWorldEnv('', serverPath=None, envStepLimit=1_000)

    return context['env']


def enrich_state(env: ScienceWorldEnv, state: dict):
    state['actions'] = env.getPossibleActions()
    state['objects'] = env.getPossibleObjects()


@app.route('/tasks', methods=['POST'])
def task_names():
    env = get_env()
    task_names = env.getTaskNames()
    tasks = {name: env.getMaxVariations(name) for name in task_names}
    status_code = 200
    return tasks, status_code


@app.route('/reset', methods=['POST'])
def reset():
    env = get_env()
    data = request.json
    name = data['name']
    variation = data['variation']
    obs, state = env.load(name, variation, generateGoldPath=True)
    desc = env.getTaskDescription()
    enrich_state(env, state)

    response = {
        'desc': desc,
        'obs': obs,
        'state': state,
    }
    status_code = 200
    return response, status_code


@app.route('/info', methods=['POST'])
def step():
    data = request.json
    action = data['action']
    step = 

