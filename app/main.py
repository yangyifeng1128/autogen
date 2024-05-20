from asyncio import gather, sleep

from fastapi import FastAPI, WebSocket

from .api.v1.urls import router as v1_router
from .api.v2.urls import router as v2_router
from .autogen.autogen_manager import AutogenManager
from .ws.socket_manager import SocketManager

app = FastAPI()

app.include_router(v1_router)
app.include_router(v2_router)

socket_manager = SocketManager()


@app.websocket("/{chat_id}")
async def socket_endpoint(
    socket: WebSocket,
    chat_id: str,
):
    try:
        autogen_manager = AutogenManager(socket=socket, chat_id=chat_id)
        await socket_manager.connect(autogen_manager)
        message = await autogen_manager.socket.receive_text()
        gather(
            send_message(autogen_manager),
            receive_message(autogen_manager),
        )
        await autogen_manager.start(message)
    except Exception as error:
        socket_manager.disconnect(autogen_manager)
        print(error)


async def send_message(autogen_manager: AutogenManager):
    while True:
        reply = await autogen_manager.client_receive_queue.get()
        if reply and reply == "DO_FINISH":
            autogen_manager.client_receive_queue.task_done()
            break
        await autogen_manager.socket.send_text(reply)
        autogen_manager.client_receive_queue.task_done()
        await sleep(0.05)


async def receive_message(autogen_manager: AutogenManager):
    while True:
        reply = await autogen_manager.socket.receive_text()
        if reply and reply == "DO_FINISH":
            await autogen_manager.client_receive_queue.put("DO_FINISH")
            await autogen_manager.client_sent_queue.put("DO_FINISH")
            break
        await autogen_manager.client_sent_queue.put(reply)
        await sleep(0.05)
