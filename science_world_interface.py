from __future__ import annotations
import dataclasses

import requests


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


SYSTEM = 'system'
USER = 'user'
ASSISTANT = 'assistant'


def make_message(role: str, content: str) -> dict[str, str]:
    return {'role': role, 'content': content}


def format_bullet_list(xs: list[str]) -> str:
    return '- ' + '\n- '.join(xs)


def convert_messages_to_str(messages: list[dict[str, str]]) -> str:
    strings = []
    for m in messages:
        header = f'{10*"-"} [ROLE: {m["role"]}] {10*"-"}'
        strings.append(header + '\n' + m['content'])

    return '\n'.join(strings)


ZERO_SHOT_SYSTEM_PROMPT = """\
You are an AI scientist. {task_description}

## Instructions:

At each step you will be given an observation and a list of valid action templates and objects. Choose the next action that will best help you complete your specified task by selecting an action template and filling in any placeholders.

### Format:

Output your selected action and a short rationale below the JSON format below:

```json
{{
   "reason": "your rationale",
   "action": "your action"
}}
```"""

ZERO_SHOT_USER_PROMPT_FIRST = """\
## Observation:

{observation}

## Objects:

{choices[objects]}

## Action Templates:

{choices[actions]}

Please choose your next action."""


ZERO_SHOT_USER_PROMPT = """\
## Observation (reward = {reward}):

{observation}

## Objects:

{choices[objects]}

## Action Templates:

{choices[actions]}

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

    def __post_init__(self):
        data = self.client.load(self.task, self.variation)
        self.format_data(data)

        system = self.system_prompt.format(**data)
        user = self.user_prompt_first.format(**data)
        self.messages.append(make_message(SYSTEM, system))
        self.messages.append(make_message(USER, user))

    def step(self, action: str, assistant: str | None = None) -> bool:
        data = self.client.step(action)
        self.format_data(data)
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
You are an AI scientist (the "agent"). {task_description}

## Instructions:

At each step you will be given an observation and a reward based on your previous action. Choose the next action that will best help you complete your specified task by selecting an action template from the option below and filling in any OBJ placeholders. Your output should consist of any reasoning, followed by your selected actions, denoted as "Action: your selected action." At each step you may select a single action only.

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
