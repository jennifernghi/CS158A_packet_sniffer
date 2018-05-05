# -*- coding: utf-8 -*-

import pcapy
import asyncio
import logging
import bencoder
from datetime import datetime

from .packets import RawPacket

logger = logging.getLogger(__name__)


class Sniffer(object):
    def __init__(self, device, loop, dump=None):
        self.device = device
        self.loop = loop
        self.dump = dump
        self.queues = []
        self.count = 0

    def parse_packet(self, packet):
        packet = RawPacket(packet)
        return packet.evolve()

    async def sniff(self):
        reader = pcapy.open_live(self.device, 65536, 0, 0)
        logger.info("Sniffing on %s", self.device)

        while True:
            (header, packet) = await self.loop.run_in_executor(None, reader.next)
            if self.dump:
                self.dump.write(bencoder.encode(packet))
            (second, ms) = header.getts()
            packet = self.parse_packet(packet).to_dict()
            packet["id"] = self.count
            packet["timestamp"] = datetime.fromtimestamp(second).strftime("%H:%M:%S") + "." + str(ms)
            self.count += 1
            await self.broadcast(packet)

    async def broadcast(self, packet):
        logger.debug("broadcasting packet: %s", packet)
        for queue in self.queues:
            await queue.put(packet)

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
            packet = self.parse_packet(packet)
            await self.broadcast(packet)

        self.loop.stop()
