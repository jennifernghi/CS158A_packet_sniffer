# -*- coding: utf-8 -*-

import unittest

from .packets import RawPacket, TCPPacket, HTTPResponsePacket, HTTPRequestPacket


class TestRawPacket(unittest.TestCase):
    def test_evolve_tcp(self):
        raw = b'\x88\xd7\xf6\xaf\xdd(<\x15\xc2\xde\xdb\xf2\x08\x00E\x00\x00\x9c\x00\x00@\x00@\x06\xe56\xc0\xa8\x01Hh\xf4*A\xf7\xf0\x01\xbb\xb6R\x1b\x00\xf3&\x16\xc2\x80\x18\x10\x006\xa5\x00\x00\x01\x01\x08\nO;@\xff\x93\x07\xa3,\x17\x03\x03\x00c\x00\x00\x00\x00\x00\x00\x01\xd1\xa3\x83\x8c>i-5\\\x96\x05\xff(\x1f\xed\x06\xfb\xd3\x92\x9e7k-\xf4\xdf\xde\xa3k\xf7\xa5\x11J\xce\xef<\xfbSS]\x18\x07-\x8a\xfb\x85\x90o\xa1\x86\x8f\xeb!\x197\x1c\xd2\x16Y\x05%\xfcxgF\xa8\x8bb\xac\xfd\xcff\xf9|\xd5Ax\xcc\xd3\x03\x9a\x8b\xdbHm\xd6v\x19\xe4\xb4d\'"'
        packet = RawPacket(raw)
        result = packet.evolve()

        self.assertIsInstance(result, TCPPacket)
        self.assertEqual(len(result.headers), 3)

    def test_evolve_http_request(self):
        raw = b'\x88\xd7\xf6\xaf\xdd(<\x15\xc2\xde\xdb\xf2\x08\x00E\x00\x01\xae\x00\x00@\x00@\x06VN\xc0\xa8\x01H@\x1e\xe0\xed\xfd!\x00P\xc0\xcfU\x8f\x0c\xe6\xd3\xd2P\x18 \x00\xa5v\x00\x00POST /protocol_1.2 HTTP/1.1\r\nAccept-Encoding: gzip\r\nConnection: keep-alive\r\nHost: post2.audioscrobbler.com\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 139\r\nKeep-Alive: 300\r\nUser-Agent: Spotify/107700338 OSX/0 (MacBookPro11,3)\r\n\r\ns=ef76f8c01dce541fd329208a43f30583&a[0]=fox+capture+plan&t[0]=Supersonic&i[0]=1525241684&o[0]=P&r[0]=&l[0]=209&b[0]=Butterfly&n[0]=11&m[0]='
        packet = RawPacket(raw)
        result = packet.evolve()

        self.assertIsInstance(result, HTTPRequestPacket)
        print(result.source)
        print(result.destination)

    def test_evolve_http_response(self):
        raw = b'<\x15\xc2\xde\xdb\xf2\\\x93\xa2\x1e\xd0]\x08\x00E\x00\x01\xb2.\x0f@\x00@\x06\x86\xdb\xc0\xa8\x01\xc3\xc0\xa8\x01H\xa3H\xfd\x1e\x9a\xb0\xc4gO\xdf.Q\x80\x18\x04\x10\xff\x8f\x00\x00\x01\x01\x08\ni\t\xa6\xbdO;T\xf1HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 310\r\n\r\n{"accountReq":"FREE","activeUser":"","availability":"NOT-AUTHORIZED","brandDisplayName":"sony_tv","deviceID":"25050c337113f16ad02fda89d9675991d3078170","deviceType":"GAMECONSOLE","modelDisplayName":"ps4","publicKey":"","remoteName":"PS4-370","spotifyError":0,"status":101,"statusString":"OK","version":"2.2.2"}'

        packet = RawPacket(raw)
        result = packet.evolve()
        self.assertIsInstance(result, HTTPResponsePacket)
