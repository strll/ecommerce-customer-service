from pathlib import Path

from atuguigu.chitchat.handler import ChitChatHandler
from atuguigu.engine.dialogue_engine import DialogueEngine
from atuguigu.plan.planner import TurnPlanner
from atuguigu.plan.turn_validator import TurnPlanValidator
from atuguigu.task.flow.loader import FlowLoader
from atuguigu.task.handler import TaskHandler
from atuguigu.knowledge.handler import KnowLedgeHandler

PROJECT_DIR = Path(__file__).resolve().parents[2]
FLOW_CONFIG_DIR = PROJECT_DIR / "flow_config"
FLOW_CONFIG_FILES = ("system_flows.yml", "user_flows.yml")


def build_dialogue_engine():


    flow_list = FlowLoader.load_many([FLOW_CONFIG_DIR / file_name for file_name in FLOW_CONFIG_FILES])

    return DialogueEngine(
        turn_planner=TurnPlanner(),
        turn_validator=TurnPlanValidator(),
        task_handler=TaskHandler(flows=flow_list),
        knowLedge_handler=KnowLedgeHandler(),
        chit_chat_handler=ChitChatHandler()
    )