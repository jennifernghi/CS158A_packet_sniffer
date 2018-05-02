# -*- coding: utf-8 -*-

import click
import pcapy
import logging
import bencoder
import coloredlogs
from packets import EthernetPacket, IPv4Packet, TCPPacket, ICMPPacket


logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")


def parse_ip_packet(ip, packet):
    logger.info("version: %d, header length: %d, protocol: %d, source: %s, dest: %s",
                ip.version, ip.length, ip.protocol, ip.source, ip.destination)

    if ip.protocol == 1:
        # ICMP
        (icmp, packet) = ICMPPacket.parse(packet)
        logger.info("ICMP: type: %d code: %d checksum: %x",
                    icmp.type_, icmp.code, icmp.checksum)
        return
    elif ip.protocol == 6:
        # TCP
        (tcp, packet) = TCPPacket.parse(packet)
        logger.info("TCP: source port: %d destination: %d",
                    tcp.source, tcp.destination)
        if tcp.source == 80 or tcp.destination == 80:
            logger.info("TCP body: %s", packet)
        return
    elif ip.protocol == 0x11:
        # UDP
        return
    logger.warning("Unknown ip protocol: %s", hex(ip.protocol))
    return


def parse_packet(packet):
    (ethernet, packet) = EthernetPacket.parse(packet)

    if ethernet.big_endian_protocol < 0x05DC:
        # IEEE 802.3 packet
        return
    elif ethernet.protocol == 0x0008:
        # IPv4
        (ip, packet) = IPv4Packet.parse(packet)
        parse_ip_packet(ip, packet)
        return
    elif ethernet.protocol == 0xdd86:
        # IPv6
        return
    elif ethernet.protocol == 0xCC88:
        # IEEE Std 802.1AB - Link Layer Discovery Protocol (LLDP)
        return
    elif ethernet.protocol == 0x0608:
        # ARP
        return
    logger.warning("Unknown ethernet protocol: %s", hex(ethernet.protocol))
    return


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
