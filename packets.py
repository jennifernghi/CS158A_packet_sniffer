# -*- coding: utf-8 -*-

import socket
import struct
import logging


logger = logging.getLogger(__name__)


class Packet(object):
    def __init__(self, **kwargs):
        for (k, w) in kwargs.items():
            setattr(self, k, w)
        self._attributes = kwargs

        if "raw_body" in kwargs:
            self.parse_body()

    def __dict__(self):
        return self._attributes


class EthernetPacket(Packet):
    @staticmethod
    def _parse_mac(binary):
        return ":".join(["{:02x}"] * 6).format(*binary)

    @classmethod
    def parse(cls, raw):
        header = struct.unpack("!6s6sH", raw[:14])
        packet = cls(destination=EthernetPacket._parse_mac(header[0]),
                     source=EthernetPacket._parse_mac(header[1]),
                     protocol=socket.ntohs(header[2]), raw_body=raw[14:])
        return packet

    def parse_body(self):
        if self.big_endian_protocol < 0x05DC:
            # IEEE 802.3 packet
            return
        elif self.protocol == 0x0008:
            # IPv4
            self.body = IPv4Packet.parse(self.raw_body)
            return
        elif self.protocol == 0xdd86:
            # IPv6
            return
        elif self.protocol == 0xCC88:
            # IEEE Std 802.1AB - Link Layer Discovery Protocol (LLDP)
            return
        elif self.protocol == 0x0608:
            # ARP
            return

    @property
    def big_endian_protocol(self):
        low = self.protocol >> 8
        high = self.protocol & 0xFF
        return (high << 8 | low)


class IPv4Packet(Packet):
    @classmethod
    def parse(cls, raw):
        header = struct.unpack("!BBHHHBBH4s4s", raw[:20])
        attributes = {}
        attributes["version"] = header[0] >> 4
        attributes["length"] = (header[0] & 0xF) * 4
        attributes["dscp"] = header[1] >> 2
        attributes["ecn"] = header[1] & 0x3
        attributes["packet_length"] = header[2]
        attributes["identification"] = header[3]
        attributes["flags"] = header[4] >> 13
        attributes["fragment_offset"] = header[4] & 0x1FFF
        attributes["ttl"] = header[5]
        attributes["protocol"] = header[6]
        attributes["checksum"] = header[7]
        attributes["source"] = socket.inet_ntoa(header[8])
        attributes["destination"] = socket.inet_ntoa(header[9])
        if attributes["length"] > 20:
            attributes["options"] = raw[20:attributes["length"]]
        attributes["raw_body"] = raw[attributes["length"]:]

        packet = cls(**attributes)

        return packet

    def parse_body(self):
        if self.protocol == 1:
            # ICMP
            self.body = ICMPPacket.parse(self.raw_body)
            logger.info("ICMP: type: %d code: %d checksum: %x",
                        self.body.type_, self.body.code, self.body.checksum)
            return
        elif self.protocol == 6:
            # TCP
            self.body = TCPPacket.parse(self.raw_body)
            logger.info("TCP: source port: %d destination: %d",
                        self.body.source, self.body.destination)
            if self.body.source == 80 or self.body.destination == 80:
                logger.info("TCP body: %s", self.body)
            return
        elif self.protocol == 0x11:
            # UDP
            return


class TCPPacket(Packet):
    @classmethod
    def parse(cls, raw):
        header = struct.unpack("!HHIIBBHHH", raw[:20])
        source = header[0]
        destination = header[1]
        sequence = header[2]
        ack = header[3]
        offset = header[4] >> 4
        ns = header[4] & 1
        flags = header[5]
        window_size = header[6]
        checksum = header[7]
        urgent = header[8]

        return cls(source=source, destination=destination, sequence=sequence,
                   ack=ack, offset=offset, ns=ns, flags=flags,
                   window_size=window_size, checksum=checksum, urgent=urgent,
                   body=raw[offset * 4:])


class ICMPPacket(Packet):
    @classmethod
    def parse(cls, raw):
        (type_, code, checksum, rest) = struct.unpack("!BBHI", raw[:8])
        return cls(type_=type_, code=code, checksum=checksum, rest=rest)
