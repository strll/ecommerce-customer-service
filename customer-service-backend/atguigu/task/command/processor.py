from typing import List

from atguigu.domain.contexts import TaskContext, StartedSystemContext, CanceledSystemContext, ResumedSystemContext, \
    InterruptedSystemContext
from atguigu.domain.state import DialogueState
from atguigu.task.command.models import Command, StartFlowCommand, SetSlotsCommand, ResumeFlowCommand, \
    CancelFlowCommand
from atguigu.task.flow.flow import FlowsList


class CommandProcessor:
    def run(self, state: DialogueState, commands: List[Command], flow_list: FlowsList):
        for command in commands:
            self._apply(state, command, flow_list)

    def _apply(self, state: DialogueState, command: Command, flow_list: FlowsList):

        if isinstance(command, StartFlowCommand):
            self._handle_start_flow(state, command, flow_list)

        elif isinstance(command, SetSlotsCommand):
            self._handle_set_slots(state, command)

        elif isinstance(command, ResumeFlowCommand):
            self._handle_resume_flow(state, flow_list, command)  # 其次复杂

        elif isinstance(command, CancelFlowCommand):
            self.handle_cancel_flow(state, flow_list)

        else:
            pass

    def _handle_set_slots(self, state: DialogueState, command: SetSlotsCommand):

        if state.active_task is not None:
            state.set_slots(command.slots)


    def handle_cancel_flow(self,
                           state: DialogueState,
                           flow_list: FlowsList):

        """
        取消当前业务流程、进入取消系统流程
        :param state:
        :param flow_list:
        :return:
        """

        # 1. 激活系统的取消流程
        task = state.active_task
        flow = flow_list.get_flow_by_id(task.flow_id)
        self._activate_cancel_system_flow(state,
                                          flow_list,
                                          cancel_flow_id=flow.id,
                                          cancel_flow_name=self._readable_flow_name(flow.id, flow_list)
                                          )
        state.end_active_task()


    def _handle_start_flow(self, state: DialogueState,
                           command: StartFlowCommand,
                           flow_list: FlowsList):

        state.end_active_task()

        target_flow = flow_list.get_flow_by_id(command.flow)

        active_task = state.active_task

        if active_task is not None:

            if active_task.flow_id == command.flow:
                return

            state.interrupted_active_task()

            if command.flow.startswith("system_"):
                raise ValueError(f"不能开启系统任务流程ID{command.flow}")

            #
            flow =flow_list.get_flow_by_id(command.flow)
            if flow is None:
                raise ValueError(f"开启的流程对应的id不存在 {command.flow}")

            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flow_list)

        # b.2) 检查自己是否在栈中
        # ①：栈中没你 需要新开，引出中断开场白
        if not state.resumed_active_task(command.flow):
            started_flow_id = command.flow
            started_flow_name = self._readable_flow_name(command.flow, flow_list)

            state.start_active_task(TaskContext(
                flow_id=target_flow.id,
                step_id=target_flow.start_step().id
            ))
        # ②：栈中有你（之前存的状态是怎样，就是怎样）不用重复开，引出中断开场白
        else:

            started_flow_id = command.flow
            started_flow_name = self._readable_flow_name(command.flow, flow_list)

        # b.2) 引出中断系统流程(中断信息的过场出来)：别人存在
        self._activate_interrupted_system_task(state, flow_list,
                                               interrupted_flow_id=interrupted_flow_id,
                                               interrupted_flow_name=interrupted_flow_name,
                                               started_flow_id=started_flow_id,
                                               started_flow_name=started_flow_name
                                               )

        return

    @staticmethod
    def _activate_interrupted_system_task(state: DialogueState,
                                          flow_list: FlowsList,
                                          *,
                                          interrupted_flow_id: str,
                                          interrupted_flow_name: str,
                                          started_flow_id: str,
                                          started_flow_name: str
                                          ):

        flow = flow_list.get_flow_by_id("system_task_interrupted")
        state.start_active_system_task(InterruptedSystemContext(
            flow_id=flow.id,
            step_id=flow.start_step().id,
            interrupted_flow_id=interrupted_flow_id,
            interrupted_flow_name=interrupted_flow_name,
            started_flow_id=started_flow_id,
            started_flow_name=started_flow_name
        ))

    @staticmethod
    def _readable_flow_name(fllow_id: str, flow_list: FlowsList) -> str:
        flow = flow_list.get_flow_by_id(fllow_id)

        return flow.name if flow.name else flow.id

    @staticmethod
    def _activate_start_system_task(state: DialogueState,
                                    flow_list: FlowsList,
                                    *,
                                    started_flow_id: str,
                                    started_flow_name: str
                                    ):

        flow = flow_list.get_flow_by_id("system_task_started")

        state.start_active_system_task(StartedSystemContext(
            flow_id=flow.id,
            step_id=flow.start_step().id,
            started_flow_id=started_flow_id,
            started_flow_name=started_flow_name
        ))

        @staticmethod
        def _activate_interrupted_system_task(state: DialogueState,
                                              flow_list: FlowsList,
                                              *,
                                              interrupted_flow_id: str,
                                              interrupted_flow_name: str,
                                              started_flow_id: str,
                                              started_flow_name: str
                                              ):

            flow = flow_list.get_flow_by_id("system_task_interrupted")
            state.start_active_system_task(InterruptedSystemContext(
                flow_id=flow.id,
                step_id=flow.start_step().id,
                interrupted_flow_id=interrupted_flow_id,
                interrupted_flow_name=interrupted_flow_name,
                started_flow_id=started_flow_id,
                started_flow_name=started_flow_name
            ))

        def _activate_resumed_system_flow(self,
                                          state: DialogueState,
                                          flow_list: FlowsList,
                                          resumed_flow_id: str,
                                          resumed_flow_name: str):

            flow = flow_list.get_flow_by_id("system_task_resumed")
            state.start_active_system_task(ResumedSystemContext(
                flow_id=flow.id,
                step_id=flow.start_step().id,
                resumed_flow_id=resumed_flow_id,
                resumed_flow_name=resumed_flow_name
            ))

        def _activate_cancel_system_flow(self,
                                         state: DialogueState,
                                         flow_list: FlowsList,
                                         *,
                                         cancel_flow_id: str,
                                         cancel_flow_name: str):

            flow = flow_list.get_flow_by_id("system_task_canceled")
            state.start_active_system_task(CanceledSystemContext(
                flow_id=flow.id,
                step_id=flow.start_step().id,
                canceled_flow_id=cancel_flow_id,
                canceled_flow_name=cancel_flow_name
            ))

        def handle_cancel_flow(self,
                               state: DialogueState,
                               flow_list: FlowsList):

            """
            取消当前业务流程、进入取消系统流程
            :param state:
            :param flow_list:
            :return:
            """

            # 1. 激活系统的取消流程
            task = state.active_task
            flow = flow_list.get_flow_by_id(task.flow_id)
            self._activate_cancel_system_flow(state,
                                              flow_list,
                                              cancel_flow_id=flow.id,
                                              cancel_flow_name=self._readable_flow_name(flow.id, flow_list)
                                              )
            state.end_active_task()

        def _handle_resume_flow(self,
                                state: DialogueState,
                                flow_list: FlowsList,
                                command: ResumeFlowCommand):

            # ===== 第一步:确定要恢复哪个流程 =====
            if command.flow is not None:
                # 指名恢复:用户明确说了恢复哪个
                target_flow = flow_list.get_flow_by_id(command.flow)
                if target_flow is None:
                    raise ValueError(f"Unknown flow '{command.flow}'.")
                target_flow_id = target_flow.id
                target_flow_name = target_flow.name
            else:
                # 不指名恢复:用户只说"继续刚才的" → 取暂停栈栈顶(最近挂起的)
                if not state.paused_tasks:
                    return
                top_paused = state.paused_tasks[-1]
                target_flow_id = top_paused.flow_id
                target_flow_name = self._readable_flow_name(target_flow_id, flow_list)

            # ===== 第二步:按"当前有没有活跃任务"恢复 =====
            active_task = state.active_task

            if active_task is not None:

                # 判断恢复的任务流程ID是否等于当前正在执行的业务任务流程ID
                if active_task.flow_id == target_flow_id:
                    return

                state.interrupted_active_task()  # 将当前正在执行的业务任务流程压入栈
                interrupted_flow_id = active_task.flow_id
                interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flow_list)

                if not state.resumed_active_task(flow_id=target_flow_id):  # 恢复失败了
                    state.resumed_active_task(flow_id=None)  # 撤销影响的那个当前正在执行的业务任务流程
                    return

                self._activate_interrupted_system_task(
                    state, flow_list,
                    interrupted_flow_id=interrupted_flow_id,
                    interrupted_flow_name=interrupted_flow_name,
                    started_flow_id=target_flow_id,
                    started_flow_name=target_flow_name,
                )
            else:
                if not state.resumed_active_task(command.flow):  # ④没任务,直接恢复
                    return

                resumed = state.active_task  # 获取从栈中恢复的业务流程
                self._activate_resumed_system_flow(
                    state, flow_list,
                    resumed_flow_id=resumed.flow_id,
                    resumed_flow_name=self._readable_flow_name(resumed.flow_id, flow_list),
                )



    def _handle_resume_flow(self,
                            state: DialogueState,
                            flow_list: FlowsList,
                            command: ResumeFlowCommand):

        # ===== 第一步:确定要恢复哪个流程 =====
        if command.flow is not None:
            # 指名恢复:用户明确说了恢复哪个
            target_flow = flow_list.get_flow_by_id(command.flow)
            if target_flow is None:
                raise ValueError(f"Unknown flow '{command.flow}'.")
            target_flow_id = target_flow.id
            target_flow_name = target_flow.name
        else:
            # 不指名恢复:用户只说"继续刚才的" → 取暂停栈栈顶(最近挂起的)
            if not state.paused_tasks:
                return
            top_paused = state.paused_tasks[-1]
            target_flow_id = top_paused.flow_id
            target_flow_name = self._readable_flow_name(target_flow_id, flow_list)

        # ===== 第二步:按"当前有没有活跃任务"恢复 =====
        active_task = state.active_task

        if active_task is not None:

            # 判断恢复的任务流程ID是否等于当前正在执行的业务任务流程ID
            if active_task.flow_id == target_flow_id:
                return

            state.interrupted_active_task()  # 将当前正在执行的业务任务流程压入栈
            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flow_list)

            if not state.resumed_active_task(flow_id=target_flow_id):  # 恢复失败了
                state.resumed_active_task()  # 撤销影响的那个当前正在执行的业务任务流程
                return

            self._activate_interrupted_system_task(
                state, flow_list,
                interrupted_flow_id=interrupted_flow_id,
                interrupted_flow_name=interrupted_flow_name,
                started_flow_id=target_flow_id,
                started_flow_name=target_flow_name,
            )
        else:
            if not state.resumed_active_task(command.flow):  # ④没任务,直接恢复
                return

            resumed = state.active_task  # 获取从栈中恢复的业务流程
            self._activate_resumed_system_flow(
                state, flow_list,
                resumed_flow_id=resumed.flow_id,
                resumed_flow_name=self._readable_flow_name(resumed.flow_id, flow_list),
            )


    def _activate_cancel_system_flow(self,
                                     state: DialogueState,
                                     flow_list: FlowsList,
                                     *,
                                     cancel_flow_id: str,
                                     cancel_flow_name: str):

        flow = flow_list.get_flow_by_id("system_task_canceled")
        state.start_active_system_task(CanceledSystemContext(
            flow_id=flow.id,
            step_id=flow.start_step().id,
            canceled_flow_id=cancel_flow_id,
            canceled_flow_name=cancel_flow_name
        ))
