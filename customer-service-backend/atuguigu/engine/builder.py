from atuguigu.engine.dialogue_engine import DialogueEngine
from atuguigu.plan.turn_planner import TurnPlanner


def build_dialogue_engine():
    return DialogueEngine(
        turn_planner=TurnPlanner()

    )