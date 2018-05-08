# -*- coding: utf-8 -*-

import http
import socket
import struct
import logging
from io import BytesIO
from binascii import hexlify
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler


logger = logging.getLogger(__name__)


def format_mac_address(binary):
    return "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(*binary)


class Header(object):
    def __init__(self, **attributes):
        self._attributes = attributes

    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError

    def __repr__(self):
        return repr(self._attributes)

    def set_summary(self, summary):
        self._attributes["_summary"] = summary


class Packet(object):
    name = ""

    def __init__(self, body, headers=None):
        self.body = body
        self.headers = []
        self.raw = []

        if headers:
            self.headers.extend(headers)

    @property
    def header(self):
        return self.headers[-1]

    @property
    def source(self):
        return None

    @property
    def destination(self):
        return None

    @property
    def info(self):
        return None

    def evolve(self):
        result = self
        while True:
            new = result._evolve()
            if not new:
                break
            result = new
        return result

    def _evolve(self):
        return None

    def to_dict(self):
        return dict(
            body=self.body,
            type=self.name,
            source=self.source,
            info=self.info,
            destination=self.destination,
            headers=[header._attributes for header in self.headers],
            raw=self.raw
        )


class RawPacket(Packet):
    name = "Raw"

    def __init__(self, raw):
        super(RawPacket, self).__init__(raw)

    def evolve(self):
        result = super(RawPacket, self).evolve()
        result.raw = list(map(int, self.body))
        return result

    def _evolve(self):
        return EthernetPacket.upgrade(self)


class EthernetPacket(Packet):
    name = "Ethernet"

    @classmethod
    def upgrade(cls, packet):
        parsed = struct.unpack("!6s6sH", packet.body[:14])
        header = Header(
            destination=format_mac_address(parsed[0]),
            source=format_mac_address(parsed[1]),
            protocol=socket.ntohs(parsed[2])
        )
        header.set_summary(
            "Ethernet II, Src: {}, Dst: {}".format(header.source, header.destination)
        )
        return cls(packet.body[14:], [header])

    @property
    def big_endian_protocol(self):
        low = self.header.protocol >> 8
        high = self.header.protocol & 0xFF
        return (high << 8 | low)

    @property
    def source(self):
        return self.header.source

    @property
    def destination(self):
        return self.header.destination

    def _evolve(self):
        if self.big_endian_protocol < 0x05DC:
            # IEEE 802.3 packet
            return
        elif self.header.protocol == 0x0008:
            # IPv4
            return IPv4Packet.upgrade(self)
        elif self.header.protocol == 0xdd86:
            # IPv6
            #return
            return IPv6Packet.upgrade(self)
        elif self.header.protocol == 0xCC88:
            # IEEE Std 802.1AB - Link Layer Discovery Protocol (LLDP)
            return
        elif self.header.protocol == 0x0608:
            # ARP
            return ARPPacket.upgrade(self)
        return None


class IPv4Packet(Packet):
    name = "IPv4"

    @classmethod
    def upgrade(cls, packet):
        raw = packet.body
        parsed = struct.unpack("!BBHHHBBH4s4s", raw[:20])
        header = Header(
            version=parsed[0] >> 4,
            length=(parsed[0] & 0xF) * 4,
            dscp=parsed[1] >> 2,
            ecn=parsed[1] & 0x3,
            packet_length=parsed[2],
            identification=parsed[3],
            flags=parsed[4] >> 13,
            fragment_offset=parsed[4] & 0x1FFF,
            ttl=parsed[5],
            protocol=parsed[6],
            checksum=parsed[7],
            source=socket.inet_ntoa(parsed[8]),
            destination=socket.inet_ntoa(parsed[9])
        )
        if header.length > 20:
            header._attributes["options"] = raw[20:header.length]
        header.set_summary(
            "Internet Protocol Version 4, Src: {}, Dst: {}".format(
                header.source, header.destination
            )
        )
        return cls(raw[header.length:], packet.headers + [header])

    @property
    def source(self):
        return self.header.source

    @property
    def destination(self):
        return self.header.destination

    def _evolve(self):
        if self.header.protocol == 1:
            # ICMP
            return ICMPPacket.upgrade(self)
        elif self.header.protocol == 6:
            # TCP
            return TCPPacket.upgrade(self)
        elif self.header.protocol == 0x11:
            # UDP
            return UDPPacket.upgrade(self)


class IPv6Packet(Packet):
    name = "IPv6"

    @classmethod
    def upgrade(cls, packet):
        raw = packet.body
        parsed = struct.unpack("!4sHBB16s16s", raw[:40])
        version = parsed[0]
        traffic_class = parsed[1]
        flow_label = parsed[2]
        payload_length = parsed[3]
        source = socket.inet_ntop(version, parsed[4])
        destination = socket.inet_ntop(version, parsed[5])
        header = Header(
            version = version,
            traffic_class = traffic_class,
            flow_label = flow_label,
            payload_length = payload_length,
            source = source,
            destination = destination

        )

        header.set_summary("Internet Protocol Version 6, Src: {}, Dst: {}".format(
            header.source, header.destination
        ))
        return cls(raw[header.length:], packet.headers + [header])

    @property
    def source(self):
        return self.header.source

    @property
    def destination(self):
        return self.header.destination

    def _evolve(self):
        if self.header.protocol == 0x3A:
            # ICMP protocol
            return ICMPPacket.upgrade(self)
        elif self.header.protocol == 6:
            # TCP
            return TCPPacket.upgrade(self)
        elif self.header.protocol == 0x11:
            # UDP
            return UDPPacket.upgrade(self)


class TCPPacket(Packet):
    name = "TCP"

    @classmethod
    def upgrade(cls, packet):
        raw = packet.body
        parsed = struct.unpack("!HHIIBBHHH", raw[:20])
        source = parsed[0]
        destination = parsed[1]
        sequence = parsed[2]
        ack = parsed[3]
        offset = parsed[4] >> 4
        ns = parsed[4] & 1
        flags = parsed[5]
        window_size = parsed[6]
        checksum = parsed[7]
        urgent = parsed[8]

        header = Header(source=source, destination=destination,
                        sequence=sequence, ack=ack, offset=offset, ns=ns,
                        flags=flags, window_size=window_size,
                        checksum=checksum, urgent=urgent)

        header.set_summary(
            "Transmission Control Protocol, Src Port: {}, Dst Port: {}, Seq: {}, Ack: {}, Len: {}".format(
                header.source, header.destination, header.sequence, header.ack, header.offset * 4
            )
        )

        return cls(raw[offset * 4:], packet.headers + [header])

    @property
    def source(self):
        return "{}:{}".format(self.headers[-2].source, self.header.source)

    @property
    def destination(self):
        return "{}:{}".format(self.headers[-2].destination, self.header.destination)

    def _evolve(self):
        if self.body.startswith(b"HTTP/1.1"):
            return HTTPResponsePacket.upgrade(self)
        elif True in [self.body.startswith(verb) for verb in HTTP_VERBS]:
            return HTTPRequestPacket.upgrade(self)
        return None


HTTP_VERBS = [b"GET", b"POST", b"PUT", b"HEAD", b"DELETE"]


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, raw):
        self.rfile = BytesIO(raw)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

    def parse(self):
        return (Header(
            command=self.command,
            path=self.path,
            request_version=self.request_version,
            headers=dict(self.headers),
        ), self.rfile.read())


class HTTPRequestPacket(Packet):
    name = "HTTP"

    @classmethod
    def upgrade(cls, packet):
        (header, body) = HTTPRequest(packet.body).parse()
        header.set_summary(
            "Hypertext Transfer Protocol Request: {} {}".format(header.command, header.path)
        )
        return cls(body, packet.headers + [header])

    @property
    def source(self):
        return "{}:{}".format(self.headers[-3].source, self.headers[-2].source)

    @property
    def destination(self):
        return "{}:{}".format(self.headers[-3].destination, self.headers[-2].destination)

    @property
    def info(self):
        return "Request {} {}".format(self.header.command, self.header.path)


class HTTPResponse(HTTPResponse):
    def makefile(self, mode):
        return None

    def __init__(self, raw):
        super(HTTPResponse, self).__init__(self)
        self.fp = BytesIO(raw)
        self.begin()
        try:
            self.body = self.read()
        except http.client.IncompleteRead as e:
            self.body = e.partial

    def parse(self):
        return (Header(
            status=self.status,
            reason=self.reason,
            headers=dict(self.headers),
        ), self.body)


class HTTPResponsePacket(Packet):
    name = "HTTP"

    @classmethod
    def upgrade(cls, packet):
        (header, body) = HTTPResponse(packet.body).parse()
        header.set_summary("Hypertext Transfer Protocol Response")
        return cls(body, packet.headers + [header])

    @property
    def source(self):
        return "{}:{}".format(self.headers[-3].source, self.headers[-2].source)

    @property
    def destination(self):
        return "{}:{}".format(self.headers[-3].destination, self.headers[-2].destination)

    @property
    def info(self):
        return "Response: {} {}  ({})".format(self.header.status, self.header.reason, self.header.headers.get("Content-Type", ""))


class ICMPPacket(Packet):
    name = "ICMP"

    @classmethod
    def upgrade(cls, packet):
        (type_, code, checksum, rest) = struct.unpack("!BBHI", packet.body[:8])
        attributes = {
            "type": type_,
            "code": code,
            "checksum": checksum,
        }
        header = Header(**attributes)
        header.set_summary("Internet Control Message Protocol, Type: {}, Code: {}".format(
            type_, code
        ))
        return cls(rest, packet.headers + [header])

    @property
    def source(self):
        return "{}".format(self.headers[-2].source)

    @property
    def destination(self):
        return "{}".format(self.headers[-2].destination)


class UDPPacket(Packet):
    name = "UDP"

    @classmethod
    def upgrade(cls, packet):

        (source, destination, length, checksum) = struct.unpack("!HHHH", packet.body[:8])
        data = packet.body[8:]

        header = Header(
            source=source,
            destination=destination,
            length=length,
            checksum=checksum
        )
        header.set_summary(
            "User Datagram Protocol, Src: {}, Dst: {}, Length: {}, checksum: {}".format(
                header.source, header.destination, header.length, header.checksum
            )
        )

        return cls(data, packet.headers + [header])

    @property
    def source(self):
        return "{}:{}".format(self.headers[-2].source, self.header.source)

    @property
    def destination(self):
        return "{}:{}".format(self.headers[-2].destination, self.header.destination)


class ARPPacket(Packet):
    name = "ARP"

    @classmethod
    def upgrade(cls, packet):
        (hardware_type, protocol_type,
         hardware_length, protocol_length,
         operation,
         sender_hardware_address, sender_protocol_address,
         target_hardware_address, target_protocol_address) = struct.unpack("HHBBH6s4s6s4s", packet.body[:28])
        data = packet.body[28:]

        sender_hardware_address = format_mac_address(sender_hardware_address)
        sender_protocol_address = socket.inet_ntoa(sender_protocol_address)
        target_hardware_address = format_mac_address(target_hardware_address)
        target_protocol_address = socket.inet_ntoa(target_protocol_address)

        header = Header(
            hardware_type=hardware_type,
            protocol_type=protocol_type,
            hardware_address_length=hardware_length,
            protocol_address_length=protocol_length,
            operation=operation,
            sender_hardware_address=sender_hardware_address,
            source=sender_protocol_address,
            target_hardware_address=target_hardware_address,
            destination=target_protocol_address
        )
        header.set_summary("Address Resolution Protocol, OPER: 0x{:02x}".format(operation))

        return cls(data, packet.headers + [header])

    @property
    def source(self):
        return self.header.source

    @property
    def destination(self):
        return self.header.destination
