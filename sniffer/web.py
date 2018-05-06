# -*- coding: utf-8 -*-

import os
import logging
import asyncio
from aiohttp import web

from .utils import BytesJSONEncoder


logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


def get_static_location(name):
    base = os.path.dirname(__file__)
    return os.path.join(base, name)


async def queue_buffer(queue):
    buff = []
    while True:
        try:
            packet = await asyncio.wait_for(queue.get(), 1)
        except asyncio.TimeoutError:
            if buff:
                yield buff
                buff = []
        else:
            buff.append(packet)

            if len(buff) >= 100:
                yield buff
                buff = []


@routes.get("/ws")
async def websocket_handler(request):
    logger.info("Received websocket connection")
    sniffer = request.app["sniffer"]

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    queue = sniffer.register()
    encoder = BytesJSONEncoder()

    async for packets in queue_buffer(queue):
        try:
            logger.info("sending out packets batch: %d", len(packets))
            encoded = list(packets)
            await ws.send_str(encoder.encode(encoded))
        except RuntimeError:
            sniffer.deregister(queue)
            logger.info("connection closed.")
        except TypeError:
            logger.exception("the packet is: %s", packets)


@routes.get("/")
async def handler(request):
    fp = open(get_static_location("web/index.html"))
    return web.Response(body=fp.read(), content_type="text/html")


@routes.get("/jq.wasm.wasm")
async def jqwasm(request):
    fp = open(get_static_location("web/vendor/jq.wasm.wasm"), "rb")
    return web.Response(body=fp.read(), content_type="application/wasm")


async def start_web_server(loop, sniffer):
    app = web.Application()
    app.add_routes(routes)
    app.router.add_static("/", path=get_static_location("web"), name="static", show_index=True)
    app["sniffer"] = sniffer
    await loop.create_server(app.make_handler(), "127.0.0.1", 8080)
    logger.info("Serving at http://127.0.0.1:8080")
