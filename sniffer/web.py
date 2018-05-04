# -*- coding: utf-8 -*-

import os
import json
import logging
from aiohttp import web


logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


def get_static_location(name):
    base = os.path.dirname(__file__)
    return os.path.join(base, name)


class BytesJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return list(map(int, o))
        return super(BytesJSONEncoder, self).default(o)


@routes.get("/ws")
async def websocket_handler(request):
    sniffer = request.app["sniffer"]

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


@routes.get("/")
async def handler(request):
    fp = open(get_static_location("web/index.html"))
    return web.Response(body=fp.read(), content_type="text/html")


async def start_web_server(loop, sniffer):
    app = web.Application()
    app.add_routes(routes)
    app.router.add_static("/", path=get_static_location("web"), name="static", show_index=True)
    app["sniffer"] = sniffer
    await loop.create_server(app.make_handler(), "127.0.0.1", 8080)
    logger.info("Serving at http://127.0.0.1:8080")
