import time

from flask import Flask, request
from scienceworld import ScienceWorldEnv


app = Flask('ScienceWorld')
context = {}


def get_env() -> ScienceWorldEnv:
    if 'env' not in context:
        context['env'] = ScienceWorldEnv('', serverPath=None, envStepLimit=1_000)

    return context['env']


def get_valid_choices(env: ScienceWorldEnv):
    actions = env.getPossibleActions()
    objects = env.getPossibleObjects()
    return {'actions': actions, 'objects': objects}


@app.route('/tasks', methods=['GET'])
def task_names():
    env = get_env()
    task_names = env.getTaskNames()
    tasks = {name: env.getMaxVariations(name) for name in task_names}
    status_code = 200
    return tasks, status_code


@app.route('/load', methods=['POST'])
def load():
    data = request.json
    env = get_env()
    name = data['name']
    variation = data['variation']
    env.load(name, variation, generateGoldPath=True)
    observation, info = env.reset()
    task_description = env.getTaskDescription()
    gold_path = env.getGoldActionSequence()
    choices = get_valid_choices(env)
    response = {
        'task_description': task_description,
        'gold_path': gold_path,
        'observation': observation,
        'info': info,
        'choices': choices,
    }
    status_code = 200
    return response, status_code


@app.route('/step', methods=['POST'])
def step():
    data = request.json
    env = get_env()
    action = data['action']
    observation, reward, complete, info = env.step(action)
    choices = get_valid_choices(env)
    response = {
        'observation': observation,
        'reward': reward,
        'complete': complete,
        'info': info,
        'choices': choices,
    }
    status_code = 200
    return response, status_code
