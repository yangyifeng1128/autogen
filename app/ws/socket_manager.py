from typing import List

from app.autogen.autogen_manager import AutogenManager


class SocketManager:

    def __init__(self):
        self.active_managers: List[AutogenManager] = []

    async def connect(self, manager: AutogenManager):
        await manager.socket.accept()
        self.active_managers.append(manager)

    def disconnect(self, manager: AutogenManager):
        manager.client_receive_queue.put_nowait("DO_FINISH")
        self.active_managers.remove(manager)
