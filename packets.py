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
                     protocol=socket.ntohs(header[2]))
        return (packet, raw[14:])

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

        return (cls(**attributes), raw[attributes["length"]:])


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

        return (cls(source=source, destination=destination, sequence=sequence,
                    ack=ack, offset=offset, ns=ns, flags=flags,
                    window_size=window_size, checksum=checksum, urgent=urgent),
                raw[offset * 4:])


class ICMPPacket(Packet):
    @classmethod
    def parse(cls, raw):
        (type_, code, checksum, rest) = struct.unpack("!BBHI", raw[:8])
        return (cls(type_=type_, code=code, checksum=checksum, rest=rest),
                raw[8:])
