from __future__ import annotations
import dataclasses
import json
from typing import Any

import requests
import tabulate


@dataclasses.dataclass
class Client:
    url: str = 'http://127.0.0.1:5000'

    def get_tasks(self):
        url = self.url + '/tasks'
        response = requests.get(url=url)
        return response.json()

    def load(self, name: str, variation: int):
        url = self.url + '/load'
        d = {'name': name, 'variation': variation}
        response = requests.post(url=url, json=d)
        return response.json()

    def step(self, action: str):
        url = self.url + '/step'
        d = {'action': action}
        response = requests.post(url=url, json=d)
        return response.json()


def format_bullet_list(xs: list[str]) -> str:
    return '\n'.join(f'- {x}' for x in xs)


def format_number_list(xs: list[str]) -> str:
    return '\n'.join(f'{i}. {x}' for i, x in enumerate(xs, start=1))


def join_pairs(xs: list[tuple[str, str]]) -> list[str]:
    return [f'{k}: {v}' for k, v in xs]


ACTION_DESCRIPTIONS = [
    ["open OBJ", "Open a container or door"],
    ["close OBJ", "Close a container or door"],
    ["activate OBJ", "Activate a device"],
    ["deactivate OBJ", "Deactivate a device"],
    ["connect OBJ to OBJ", "Connect electrical components"],
    ["disconnect OBJ", "Disconnect electrical components"],
    ["use OBJ", "Use a device/item"],
    ["use OBJ on OBJ", "Use a device/item on another device/item"],
    ["look around", "Describe the current room"],
    ["look at OBJ", "Describe an object in detail"],
    ["look in OBJ", "Describe a container’s contents"],
    ["read OBJ", "Read a note or book"],
    ["move OBJ to OBJ", "Move an object to a container"],
    ["pick up OBJ", "Move an object to the inventory"],
    ["put down OBJ", "Drop an inventory item"],
    ["pour OBJ into OBJ", "Pour a liquid into a container"],
    ["dunk OBJ into OBJ", "Dunk a container into a liquid"],
    ["mix OBJ", "Chemically mix a container"],
    ["go to LOC", "Move agent to a new location"],
    ["eat OBJ", "Eat a food"],
    ["flush OBJ", "Flush a toilet"],
    ["focus on OBJ", "Signal intent on a task object"],
    ["wait1", "Wait for 1 iteration"],
    ["wait", "Wait for 10 iteration"],
    ["task", "Describe current task"],
    ["inventory", "List agent’s inventory"],
]

ACTION_TABLE = tabulate.tabulate(
    ACTION_DESCRIPTIONS,
    headers=['Action Template', 'Effect'],
    tablefmt='github',
)

ACTION_LIST = format_number_list(join_pairs(ACTION_DESCRIPTIONS))


def convert_action_description_to_json_template(action: str, description: str) -> str:
    words = action.split()
    placeholders = {}

    names = 'XYZABCQRS'
    while True:
        try:
            i = next(i for i, w in enumerate(words) if w == 'LOC' or w == 'OBJ')
        except StopIteration:
            break

        k = names[0]
        names = names[1:]
        words[i] = k
        placeholders[k] = '?'

    # if 'LOC' in words:
    #     placeholders['LOC'] = '?'

    # num_objs = sum(1 for w in words if w == 'OBJ')
    # if num_objs == 1:
    #     placeholders['OBJ'] = '?'
    # elif num_objs > 0:
    #     i = 1
    #     while 'OBJ' in words:
    #         k = f'OBJ_{i}'
    #         placeholders[k] = '?'
    #         words[words.index('OBJ')] = k
    #         i += 1

    template = json.dumps({'action': ' '.join(words), **placeholders}, ensure_ascii=False)
    return f'{description[0].upper()}{description[1:]}: `{template}`'


ACTION_JSON_TEMPLATES = format_number_list(
    convert_action_description_to_json_template(k, v) for k, v in ACTION_DESCRIPTIONS
)


SPECIAL_ACTION_DESCRIPTIONS = [
    ["teleport to LOC", "Teleport to a specific room"],
]

SPECIAL_ACTION_TABLE = tabulate.tabulate(
    SPECIAL_ACTION_DESCRIPTIONS,
    headers=['Action Template', 'Effect'],
    tablefmt='github',
)

FULL_ACTION_TABLE = tabulate.tabulate(
    ACTION_DESCRIPTIONS + SPECIAL_ACTION_DESCRIPTIONS,
    headers=['Action Template', 'Effect'],
    tablefmt='github',
)


SYSTEM = 'system'
USER = 'user'
ASSISTANT = 'assistant'


def make_message(role: str, content: str) -> dict[str, str]:
    return {'role': role, 'content': content}


def convert_messages_to_str(messages: list[dict[str, str]]) -> str:
    strings = []
    for m in messages:
        header = f'{10*"-"} [ROLE: {m["role"]}] {10*"-"}'
        strings.append(header + '\n' + m['content'])

    return '\n'.join(strings)


ZERO_SHOT_SYSTEM_PROMPT = """\
You are an AI scientist (the "agent") interacting with an environment through a text interface. {task_description}

## Instructions:

At each step, you will be given an observation and a reward based on your previous action. Choose the next action to execute that will best help you complete your task.

The table below list all valid action templates that will be recognized by the input system. The terms "OBJ", "LOC", and "DURATION" in the table represent variables. Variable names should be replaced with a valid values based on your current environment when choosing an action.

Your output should consist of your reasoning followed by your selected action on a single line with the format "Action: your selected action". Do not include unbound variables in your action. At each step you may select a single action.

{action_table}"""

ZERO_SHOT_USER_PROMPT_FIRST = """\
{observation}

Please choose your next action."""


ZERO_SHOT_USER_PROMPT = """\
(reward: {reward}, score: {info[score]}, complete: {complete})

{observation}

Please choose your next action."""


@dataclasses.dataclass
class Episode_ZeroShot:
    client: Client
    task: str
    variation: int
    system_prompt: str = ZERO_SHOT_SYSTEM_PROMPT
    user_prompt_first: str = ZERO_SHOT_USER_PROMPT_FIRST
    user_prompt: str = ZERO_SHOT_USER_PROMPT
    messages: list[dict[str, str]] = dataclasses.field(default_factory=list)
    data: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        data = self.client.load(self.task, self.variation)
        self.format_data(data)
        self.data = data

        system = self.system_prompt.format(
            **data,
            action_table=ACTION_TABLE,
            action_list=ACTION_LIST,
            action_json_templates=ACTION_JSON_TEMPLATES,
        )
        user = self.user_prompt_first.format(**data)
        self.messages.append(make_message(SYSTEM, system))
        self.messages.append(make_message(USER, user))

    def step(self, action: str, assistant: str | None = None) -> bool:
        data = self.client.step(action)
        self.format_data(data)
        self.data = data

        assistant = assistant or action
        self.messages.append(make_message(ASSISTANT, assistant))
        user = self.user_prompt.format(**data)
        self.messages.append(make_message(USER, user))

        if data['complete']:
            print('Task complete')
            return True

        return False

    @staticmethod
    def format_data(data):
        data['choices']['objects'] = format_bullet_list(data['choices']['objects'])
        data['choices']['actions'] = format_bullet_list(data['choices']['actions'])


ZERO_SHOT_DYNAMIC_SYSTEM_SYSTEM_PROMPT = """\
You are an AI scientist (the "agent") interacting with a simulation. {task_description}

## Instructions:

At each step of the simulation you will be given an observation and a reward based on your previous action. The action templates and objects below will then be updated based on the state of the simulation.

Choose your action by selecting an action template and filling in any OBJ placeholders with appropriate values. Your selected action must exactly match the form of the template or it will not be recognized by the simulation. At each step you may select a single action only.

Your output should consist of any reasoning followed by your selected action on a single line as "Action: your selected action."

## Objects:

{choices[objects]}

## Action Templates:

{choices[actions]}"""

ZERO_SHOT_DYNAMIC_SYSTEM_USER_PROMPT_FIRST = """\
{observation}

Please choose your next action."""

ZERO_SHOT_DYNAMIC_SYSTEM_USER_PROMPT = """\
reward: {reward}

{observation}

Please choose your next action."""


@dataclasses.dataclass
class Episode_ZeroShotDynamicSystem:
    client: Client
    task: str
    variation: int
    system_prompt: str = ZERO_SHOT_DYNAMIC_SYSTEM_SYSTEM_PROMPT
    user_prompt_first: str = ZERO_SHOT_DYNAMIC_SYSTEM_USER_PROMPT_FIRST
    user_prompt: str = ZERO_SHOT_DYNAMIC_SYSTEM_USER_PROMPT
    messages: list[dict[str, str]] = dataclasses.field(default_factory=list)
    task_description: str = ''

    def __post_init__(self):
        data = self.client.load(self.task, self.variation)
        self.format_data(data)

        self.task_description = data['task_description']

        system = self.system_prompt.format(**data)
        user = self.user_prompt_first.format(**data)
        self.messages.append(make_message(SYSTEM, system))
        self.messages.append(make_message(USER, user))

    def step(self, action: str, assistant: str | None = None) -> bool:
        data = self.client.step(action)
        self.format_data(data)

        system = self.system_prompt.format(task_description=self.task_description, **data)
        self.messages[0] = make_message(SYSTEM, system)

        assistant = assistant or action
        self.messages.append(make_message(ASSISTANT, assistant))
        user = self.user_prompt.format(**data)
        self.messages.append(make_message(USER, user))

        if data['complete']:
            print('Complete is True:', data['complete'])
            return True

        return False

    @staticmethod
    def format_data(data):
        data['choices']['objects'] = format_bullet_list(data['choices']['objects'])
        data['choices']['actions'] = format_bullet_list(data['choices']['actions'])
