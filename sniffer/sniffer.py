# -*- coding: utf-8 -*-

import pcapy
import asyncio
import logging
import bencoder
from datetime import datetime
from itertools import islice

from .packets import RawPacket

logger = logging.getLogger(__name__)


class Sniffer(object):
    def __init__(self, device, loop, dump=None):
        self.device = device
        self.loop = loop
        self.dump = dump
        self.queues = []
        self.count = 0

    def parse_packet(self, packet, second, ms):
        packet = RawPacket(packet)
        packet = packet.evolve().to_dict()
        packet["id"] = self.count
        self.count += 1
        packet["timestamp"] = datetime.fromtimestamp(second).strftime("%H:%M:%S") + "." + str(ms)
        return packet

    async def sniff(self):
        reader = pcapy.open_live(self.device, 65536, 0, 0)
        logger.info("Sniffing on %s", self.device)

        while True:
            (header, packet) = await self.loop.run_in_executor(None, reader.next)
            (second, ms) = header.getts()
            if self.dump:
                self.dump.write(bencoder.encode(packet))
                self.dump.write(bencoder.encode(second))
                self.dump.write(bencoder.encode(ms))

            packet = self.parse_packet(packet, second, ms)
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


def window(iterable, size=2):
    shiftedStarts = [islice(iterable, s, None, size) for s in range(size)]
    return zip(*shiftedStarts)


class DumpFileLoader(Sniffer):
    def __init__(self, fp, loop):
        super(DumpFileLoader, self).__init__('en0', loop)
        self.fp = fp
        self.connections = asyncio.Queue()

    async def sniff(self):
        content = b"l" + self.fp.read() + b"e"
        packets = bencoder.decode(content)

        while True:
            queue = await self.connections.get()
            self.count = 0
            for (packet, second, ms) in window(packets, 3):
                packet = self.parse_packet(packet, second, ms)
                await queue.put(packet)

    def register(self):
        queue = super(DumpFileLoader, self).register()
        self.connections.put_nowait(queue)
        return queue
