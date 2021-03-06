# -*- coding: utf-8 -*-

import http
import socket
import struct
import logging
from io import BytesIO
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler


logger = logging.getLogger(__name__)


class Packet(object):
    def __init__(self, **kwargs):
        #print("in init")
        #print(kwargs)
        for (k, w) in kwargs.items():
            setattr(self, k, w)
        self._attributes = kwargs
        self.body = None

        if "_raw_body" in kwargs:
            #print("have _raw_body")
            self.parse_body()

    def to_dict(self):
        #print("in to_dict")
        attrs = dict((k, v) for (k, v) in self._attributes.items()
                     if not k.startswith("_"))

        if isinstance(self.body, bytes):
            attrs["body"] = self.body
        elif self.body:
            attrs["body"] = self.body.to_dict()

        return attrs

    def __repr__(self):
        #print("in __repr__")
        return str(self.to_dict())

    @property
    def raw_body(self):
        return getattr(self, "_raw_body", None)


class EthernetPacket(Packet):
    name = "ethernet"

    @staticmethod
    def _parse_mac(binary):
        #print("in EthernetPacket _parse_mac")
        return ":".join(["{:02x}"] * 6).format(*binary)

    @classmethod
    def parse(cls, raw):
        #print("in EthernetPacket parse")
        header = struct.unpack("!6s6sH", raw[:14])
        packet = cls(destination=EthernetPacket._parse_mac(header[0]),
                     source=EthernetPacket._parse_mac(header[1]),
                     protocol=socket.ntohs(header[2]), _raw_body=raw[14:])
        return packet

    def parse_body(self):
        #print("in EthernetPacket parse_body")
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
    name = "IPv4"

    @classmethod
    def parse(cls, raw):
        #print("in IPv4Packet parse")
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
        attributes["_raw_body"] = raw[attributes["length"]:]

        packet = cls(**attributes)

        return packet

    def parse_body(self):
        #print("in IPv4Packet parse_body")
        if self.protocol == 1:
            # ICMP
            #print("in IPv4Packet ICMP")
            self.body = ICMPPacket.parse(self.raw_body)
            logger.info("ICMP: type: %d code: %d checksum: %x",
                        self.body.type_, self.body.code, self.body.checksum)
            return
        elif self.protocol == 6:
            # TCP
            #print("in IPv4Packet TCP")
            self.body = TCPPacket.parse(self.raw_body)
            logger.info("TCP: source port: %d destination: %d",
                        self.body.source, self.body.destination)
            if self.body.source == 80 or self.body.destination == 80:
                # logger.info("TCP body: %s", self.body.body)
                pass
            return
        elif self.protocol == 0x11:
            #print("in IPv4Packet UDP")
            #logger.info("UDP: source port: %d destination port: %d length: %d checksum : %d",
             #           self.body.UDP_source, self.body.UDP_destination, self.body.UDP_length, self.body.UDP_checksum)
            # UDP
            self.body = UDPPacket.parse(self.raw_body)
            return



class TCPPacket(Packet):
    name = "TCP"

    @classmethod
    def parse(cls, raw):
        #print("in TCPPacket parse")
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
                   _raw_body=raw[offset * 4:])

    def parse_body(self):
        #print("in TCPPacket parse_body")
        if self.raw_body.startswith(b"HTTP/1.1"):
            self.body = HTTPResponsePacket(self.raw_body)
        elif True in [self.raw_body.startswith(verb) for verb in HTTP_VERBS]:
            self.body = HTTPRequestPacket(self.raw_body)
        else:
            self.body = self.raw_body


HTTP_VERBS = [b"GET", b"POST", b"PUT", b"HEAD", b"DELETE"]


class HTTPRequestPacket(BaseHTTPRequestHandler):
    def __init__(self, raw):
        self.rfile = BytesIO(raw)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

    def to_dict(self):
        return dict(
            command=self.command,
            path=self.path,
            request_version=self.request_version,
            headers=dict(self.headers),
        )


class HTTPResponsePacket(HTTPResponse):
    def makefile(self, mode):
        return None

    def __init__(self, raw):
        super(HTTPResponsePacket, self).__init__(self)
        self.fp = BytesIO(raw)
        self.begin()
        try:
            self.body = self.read()
        except http.client.IncompleteRead as e:
            self.body = e.partial

    def to_dict(self):
        return dict(
            status=self.status,
            reason=self.reason,
            headers=dict(self.headers),
            body=self.body,
        )


class ICMPPacket(Packet):
    name = "ICMP"

    @classmethod
    def parse(cls, raw):
        #print("in ICMPPacket parse")
        (type_, code, checksum, rest) = struct.unpack("!BBHI", raw[:8])
        return cls(type_=type_, code=code, checksum=checksum, rest=rest)


class UDPPacket(Packet):
    name = "UDP"

    @classmethod
    def parse(cls, raw):
        #print("in UDPPacket parse")
        source, destination, length, checksum = struct.unpack("!HHHH", raw[:8])
        data = raw[8:]

        return cls(source=source, destination=destination, length=length, checksum=checksum, data=data)

