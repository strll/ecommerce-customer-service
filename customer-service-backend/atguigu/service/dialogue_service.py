from atguigu.domain.messages import UserMessage, ProcessResult
from atguigu.domain.state import DialogueState
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_state_repository import DialogueStateRepository


class DialogueService:
    def __init__(self,
                 dialogue_state_repository: DialogueStateRepository,
                 dialogue_engine: DialogueEngine):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def handle_message(self, user_message: UserMessage) -> ProcessResult:
        # 1. 通过 repository 根据 sender_id 加载对话状态
        state: DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)
        # 2. 使用 engine 根据对话状态处理最新消息
        process_result: ProcessResult = await self.dialogue_engine.hand_dialogue(state, user_message)
        # 3. 通过 repository 保存最新的对话状态
        await self.dialogue_state_repository.save_state(state)
        # 4. 返回本轮处理结果
        return process_result