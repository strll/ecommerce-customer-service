import json

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.domain.state import DialogueState
from atuguigu.models.dialogue_state import DialogueStateRecord


class DialogueStateRepository:

    def __init__(self,session: AsyncSession):
        self.session = session

    async def load(self, sender_id: str) -> dict:
        """
        加载对话状态
        :param sender_id: 用户id
        :return:
        """
        sql=(select(DialogueStateRecord)
             .where(DialogueStateRecord.sender_id == sender_id))

        result=await self.session.execute(sql)

        state = result.scalar_one_or_none()

        if state:
            json.loads(state.state_json)
            return DialogueState(
                sender_id=state.sender_id,
                state_json=state.state_json
            )


    async def save(self,dialogue_state: DialogueState):

        state_json: str = json.dumps(dialogue_state.to_dict())

        insert_stmt=insert(DialogueStateRecord).values(
            sender_id=dialogue_state.sender_id,
            state_json=state_json
        )
        update_stmt=insert_stmt.on_duplicate_key_update(
            state_json=insert_stmt.inserted.state_json
        )

        await self.session.execute(update_stmt)

        await self.session.commit()