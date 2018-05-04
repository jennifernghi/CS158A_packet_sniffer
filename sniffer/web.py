# -*- coding: utf-8 -*-

import json
import logging
from aiohttp import web


logger = logging.getLogger(__name__)
routes = web.RouteTableDef()
sniffer = None


class BytesJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return list(map(int, o))
        return super(BytesJSONEncoder, self).default(o)


@routes.get('/ws')
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    queue = sniffer.register()
    encoder = BytesJSONEncoder()

    while True:
        packet = await queue.get()
        logger.info("loop got packet: %s", packet)
        try:
            await ws.send_str(encoder.encode(packet.to_dict()))
        except RuntimeError:
            sniffer.deregister(queue)
            logger.info("connection closed.")
        except TypeError:
            logger.exception("the packet is: %s", packet)


@routes.get('/')
async def handler(request):
    return web.Response(text="ok")


async def start_web_server(loop, _sniffer):
    global sniffer
    sniffer = _sniffer
    app = web.Application()
    app.add_routes(routes)
    await loop.create_server(app.make_handler(), "127.0.0.1", 8080)
    logger.info("Serving at http://127.0.0.1:8080")
