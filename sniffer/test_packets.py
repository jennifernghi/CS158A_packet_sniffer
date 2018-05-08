# -*- coding: utf-8 -*-

import unittest

from .packets import RawPacket, TCPPacket, HTTPResponsePacket, HTTPRequestPacket, ARPPacket


class TestRawPacket(unittest.TestCase):
    def test_evolve_tcp(self):
        raw = b'\x88\xd7\xf6\xaf\xdd(<\x15\xc2\xde\xdb\xf2\x08\x00E\x00\x00\x9c\x00\x00@\x00@\x06\xe56\xc0\xa8\x01Hh\xf4*A\xf7\xf0\x01\xbb\xb6R\x1b\x00\xf3&\x16\xc2\x80\x18\x10\x006\xa5\x00\x00\x01\x01\x08\nO;@\xff\x93\x07\xa3,\x17\x03\x03\x00c\x00\x00\x00\x00\x00\x00\x01\xd1\xa3\x83\x8c>i-5\\\x96\x05\xff(\x1f\xed\x06\xfb\xd3\x92\x9e7k-\xf4\xdf\xde\xa3k\xf7\xa5\x11J\xce\xef<\xfbSS]\x18\x07-\x8a\xfb\x85\x90o\xa1\x86\x8f\xeb!\x197\x1c\xd2\x16Y\x05%\xfcxgF\xa8\x8bb\xac\xfd\xcff\xf9|\xd5Ax\xcc\xd3\x03\x9a\x8b\xdbHm\xd6v\x19\xe4\xb4d\'"'
        packet = RawPacket(raw)
        result = packet.evolve()

        self.assertIsInstance(result, TCPPacket)
        self.assertEqual(len(result.headers), 3)

    def test_evolve_http_request(self):
        raw = b"\x88\xd7\xf6\xaf\xdd(<\x15\xc2\xde\xdb\xf2\x08\x00E\x00\x02\xd9\x00\x00@\x00@\x06\xf9\xc0\xc0\xa8\x01H\xd1W\xab\x16\xdcA\x00P\x7fz\xf2\x9d'\xbe_\xdb\x80\x18\x10\x00f\x91\x00\x00\x01\x01\x08\n^\xbbWc\x02\xcf@2GET /PopCalendar2008/CSS/ADXPublic_Images/left1.gif HTTP/1.1\r\nHost: events.sjsu.edu\r\nConnection: keep-alive\r\nUser-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36\r\nAccept: image/webp,image/apng,image/*,*/*;q=0.8\r\nDNT: 1\r\nReferer: http://events.sjsu.edu/EventList.aspx?view=EventDetails&eventidn=24663&information_id=41002&type=&syndicate=syndicate\r\nAccept-Encoding: gzip, deflate\r\nAccept-Language: en-US,en;q=0.9,zh;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6\r\nCookie: __utma=69758162.1396097625.1508958142.1508999758.1510159301.2; _ga=GA1.2.1396097625.1508958142; ASP.NET_SessionId=gq1lge55aiatjdipvox5vlqe\r\n\r\n"
        packet = RawPacket(raw)
        result = packet.evolve()

        self.assertIsInstance(result, HTTPRequestPacket)

    def test_evolve_http_response(self):
        raw = b'<\x15\xc2\xde\xdb\xf2\\\x93\xa2\x1e\xd0]\x08\x00E\x00\x01\xb2.\x0f@\x00@\x06\x86\xdb\xc0\xa8\x01\xc3\xc0\xa8\x01H\xa3H\xfd\x1e\x9a\xb0\xc4gO\xdf.Q\x80\x18\x04\x10\xff\x8f\x00\x00\x01\x01\x08\ni\t\xa6\xbdO;T\xf1HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 310\r\n\r\n{"accountReq":"FREE","activeUser":"","availability":"NOT-AUTHORIZED","brandDisplayName":"sony_tv","deviceID":"25050c337113f16ad02fda89d9675991d3078170","deviceType":"GAMECONSOLE","modelDisplayName":"ps4","publicKey":"","remoteName":"PS4-370","spotifyError":0,"status":101,"statusString":"OK","version":"2.2.2"}'

        packet = RawPacket(raw)
        result = packet.evolve()
        self.assertIsInstance(result, HTTPResponsePacket)

    def test_evolve_arp(self):
        raw = b'\xff\xff\xff\xff\xff\xff0\xe4\xdb9;\xc0\x08\x06\x00\x01\x08\x00\x06\x04\x00\x01d\xb0\xa63\xc7\xbd\n\xfa\x99\xa3\x00\x00\x00\x00\x00\x00\n\xfa\x99\xa3'

        packet = RawPacket(raw)
        result = packet.evolve()
        self.assertIsInstance(result, ARPPacket)
