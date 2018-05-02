# -*- coding: utf-8 -*-

import click
import pcapy
import asyncio
import logging
import bencoder
import websockets
import coloredlogs
from packets import EthernetPacket
from websockets.exceptions import ConnectionClosed


logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")


def parse_packet(packet):
    packet = EthernetPacket.parse(packet)
    return packet


class Sniffer(object):
    def __init__(self, device, loop, dump=None):
        self.device = device
        self.loop = loop
        self.dump = dump
        self.queues = []

    async def sniff(self):
        reader = pcapy.open_live(self.device, 65536, 0, 0)
        logger.info("Sniffing on %s", self.device)

        while True:
            (header, packet) = await self.loop.run_in_executor(None, reader.next)
            if self.dump:
                self.dump.write(bencoder.encode(packet))
            packet = parse_packet(packet)
            logger.info("caught: %s", packet)
            await self.broadcast(packet)

    async def broadcast(self, packet):
        logger.info("broadcasting packet: %s", packet)
        for queue in self.queues:
            await queue.put("test")

    def register(self):
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue(loop=loop)
        self.queues.append(queue)
        logger.debug("queue registered.")
        return queue

    def deregister(self, queue):
        self.queues.remove(queue)
        logger.debug("queue deregistered.")


class DumpFileLoader(Sniffer):
    def __init__(self, fp, loop):
        super(DumpFileLoader, self).__init__('en0', loop)
        self.fp = fp

    async def sniff(self):
        content = b"l" + self.fp.read() + b"e"
        packets = bencoder.decode(content)
        for packet in packets:
            packet = parse_packet(packet)
            await self.broadcast(packet)

        self.loop.stop()


def start_websocket_server(sniffer):
    async def websocket_loop(websocket, path):
        queue = sniffer.register()
        while True:
            packet = await queue.get()
            logger.info("loop got packet: %s", packet)
            try:
                await websocket.send(packet)
            except ConnectionClosed:
                sniffer.deregister(queue)
                logger.info("connection closed.")

    logger.info("Starting WebSocket server at ws://127.0.0.1:5678")
    return websockets.serve(websocket_loop, '127.0.0.1', 5678)


@click.command()
@click.option("--device", "-d", default="en0", help="network device you want to sniff at")
@click.option("--dump", type=click.File("wb"), help="dump traffic to this file")
@click.option("--load", type=click.File("rb"), help="traffic dump file to load")
def main(device, dump, load):
    loop = asyncio.get_event_loop()
    futures = []

    if load:
        sniffer = DumpFileLoader(load, loop)
    else:
        sniffer = Sniffer(device, loop, dump=dump)

    futures.append(sniffer.sniff())
    futures.append(start_websocket_server(sniffer))

    loop.run_until_complete(asyncio.gather(*futures))
    loop.run_forever()


if __name__ == "__main__":
    exit(main())
