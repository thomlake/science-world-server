# ScienceWorld Server

> Simple Flask server for interacting with the [ScienceWorld](https://github.com/allenai/ScienceWorld) environment.

## Setup

Step 1: Install ScienceWorld and Flask

```
conda create --name scienceworld python=3.8
conda activate scienceworld
pip install scienceworld
pip install flask
```

Step 2: Launch Server
```
cd science-world-server
flask run
```

Step 3: Interact with Server

```python
import science_world_interface as swi

client = swi.Client()
name, variation = 'find-animal', 0
episode = swi.ZeroShotEpisode(client, name, variation)
print(json.dumps(episode.messages, indent=2))
```

```json
[
  {
    "role": "system",
    "content": "You are an AI scientist. Your task is to find a(n) animal. First, focus on the thing. Then, move it to the red box in the kitchen.\n\n## Instructions:\n\nAt each step you will be given an observation and a list of valid action templates and objects. Choose the next action that will best help you complete your specified task by selecting an action template and filling in any placeholders.\n\n### Format:\n\nOutput your selected action and a short rationale below the JSON format below:\n\n```json\n{\n   \"reason\": \"your rationale\",\n   \"action\": \"your action\"\n}\n```"
  },
  {
    "role": "user",
    "content": "## Observation:\n\nThis room is called the hallway. In it, you see: \n\tthe agent\n\ta substance called air\n\ta picture\nYou also see:\n\tA door to the art studio (that is closed)\n\tA door to the bedroom (that is closed)\n\tA door to the greenhouse (that is closed)\n\tA door to the kitchen (that is closed)\n\tA door to the living room (that is closed)\n\tA door to the workshop (that is closed)\n\n## Objects:\n\n- agent\n- air\n- art studio\n- art studio door\n- bedroom\n- bedroom door\n- door to greenhouse\n- door to kitchen\n- door to living room\n- door to workshop\n- greenhouse\n- hallway\n- kitchen\n- living room\n- picture\n- workshop\n\n## Action Templates:\n\n- activate OBJ\n- close OBJ\n- connect OBJ to OBJ\n- deactivate OBJ\n- disconnect OBJ\n- dunk OBJ in OBJ\n- eat OBJ\n- flush OBJ\n- focus on OBJ\n- go OBJ\n- inventory\n- look around\n- look at OBJ\n- look in OBJ\n- mix OBJ\n- move OBJ to OBJ\n- open OBJ\n- pick up OBJ\n- pour OBJ in OBJ\n- put down OBJ\n- read OBJ\n- reset task\n- task\n- use OBJ on OBJ\n- wait\n- wait1\n\nPlease choose your next action."
  }
]
```
