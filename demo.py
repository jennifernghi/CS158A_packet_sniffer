# -*- coding: utf-8 -*-

import click
import pcapy
import logging
import bencoder
import coloredlogs
from packets import EthernetPacket, IPv4Packet, TCPPacket, ICMPPacket


logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")


def parse_packet(packet):
    packet = EthernetPacket.parse(packet)
    print(packet)


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
