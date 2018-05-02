# -*- coding: utf-8 -*-

import sys
import click
import pcapy
import logging
import bencoder
from packets import EthernetPacket, Ipv4Packet


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_packet(packet):
    (ethernet, packet) = EthernetPacket.parse(packet)

    if ethernet.protocol != 8:
        return

    (ip, packet) = Ipv4Packet.parse(packet)

    logger.info("version: %d, header length: %d, protocol: %d, source: %s, dest: %s",
                ip.version, ip.length, ip.protocol, ip.source, ip.destination)
    logger.info("packet length: %d", ip.packet_length)


def parse_dump_file(dump):
    # TODO: need to replace bencode as it requires reading the whole dump file
    # into memeory.
    content = b"l" + dump.read() + b"e"
    packets = bencoder.decode(content)

    for packet in packets:
        parse_packet(packet)


@click.command()
@click.option("--device", "-d", default="en0", help="network device you want to sniff at")
@click.option("--dump", type=click.File("wb"), help="dump traffic to this file")
@click.option("--load", type=click.File("rb"), help="traffic dump file to load")
def main(device, dump, load):
    if load:
        return parse_dump_file(load)

    reader = pcapy.open_live(device, 65536, 0, 0)
    logger.info("Sniffing on %s", device)

    while True:
        (header, packet) = reader.next()
        logger.debug("captured %s bytes, truncated %s bytes, real length %s",
                     header.getlen(), header.getcaplen(), len(packet))
        if dump:
            dump.write(bencoder.encode(packet))
        parse_packet(packet)


if __name__ == "__main__":
    exit(main())
