import importlib
import inspect
import pkgutil

from atguigu.task.action.base import Action
from atguigu.task.action.buitin.listener import ActionListener
from atguigu.task.action.buitin.registry import ActionRegistry
from atguigu.task.action.buitin.response import ActionResponse
from atguigu.task.action.buitin.runner import ActionRunner


def register_builtin_action(action_runner: ActionRunner) -> Action:



    action_listener = ActionListener()
    action_response = ActionResponse()

    action_runner.registry.register(action_listener)
    action_runner.registry.register(action_response)


def register_custom_action(action_runner: ActionRunner):
    package = importlib.import_module("atguigu.task.action.customer")

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, prefix=f"{package.__name__}."):

        if is_pkg:
            continue
        module = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, Action) or obj is Action:
                continue
            if obj.__module__ != module.__name__:
                continue
            action_runner.registry.register(obj())



def build_action_runner() -> ActionRunner:
    action_runner = ActionRunner(
        ActionRegistry()
    )

    return action_runner
