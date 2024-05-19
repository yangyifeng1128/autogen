"""Socket连接管理器"""

from typing import List

from app.autogen.autogen_manager import AutogenManager


class SocketManager:
    """Socket连接管理器"""

    def __init__(self):
        """初始化Socket连接管理器"""
        self.active_managers: List[AutogenManager] = []

    async def connect(self, manager: AutogenManager):
        """连接Socket服务器"""
        await manager.socket.accept()
        self.active_managers.append(manager)

    def disconnect(self, manager: AutogenManager):
        """断开Socket服务器"""
        manager.client_receive_queue.put_nowait("DO_FINISH")
        self.active_managers.remove(manager)
