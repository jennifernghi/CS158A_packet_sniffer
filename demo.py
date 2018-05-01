# -*- coding: utf-8 -*-

import sys
import pcapy
import socket
import struct
import logging


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(device="en0"):
    reader = pcapy.open_live(device, 65536, 0, 0)
    logger.info("Sniffing on %s", device)
    while True:
        (header, packet) = reader.next()
        logger.info("captured %s bytes, truncated %s bytes",
                    header.getlen(), header.getcaplen())
        parse_packet(packet)


def convert_mac(data):
    return ":".join(["{:02x}"] * 6).format(*data)


def parse_packet(packet):
    eth = struct.unpack('!6s6sH', packet[:14])
    protocol = socket.ntohs(eth[2])
    logger.info("dest: %s, source: %s protocol: %d",
                convert_mac(packet[:6]), convert_mac(packet[6:12]), protocol)

    if protocol != 8:
        return

    ip_header = struct.unpack('!BBHHHBBH4s4s', packet[14:34])
    version = ip_header[0] >> 4
    length = (ip_header[0] & 0xF) * 4
    source = socket.inet_ntoa(ip_header[8])
    dest = socket.inet_ntoa(ip_header[9])

    logger.info("version: %d, header length: %d, protocol: %d, source: %s, dest: %s",
                version, length, protocol, source, dest)


if __name__ == '__main__':
    exit(main())
