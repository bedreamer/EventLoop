# -*- coding: utf8 -*-
import thttpd
import HttpRespons
import hashlib
import base64
import time
import struct


class WebSocketRespons(HttpRespons.HttpRespons):
    def __init__(self, request, body=None, headers=None, code=None):
        super(WebSocketRespons, self).__init__(body, headers, code)
        self.headers = dict()
        self.set_header('Connection', 'Upgrade')
        self.set_header('Upgrade', 'websocket')
        if hasattr(request, "sec_websocket_key"):
            secure_ack_key = self.calc_secure_key(request.sec_websocket_key)
        else:
            secure_ack_key = ''
        self.set_header('Sec-WebSocket-Accept', secure_ack_key)

        '''
        if hasattr(request, "sec_websocket_extensions"):
            self.set_header('Sec-WebSocket-Extensions', request.sec_websocket_extensions)

        if hasattr(request, "sec_websocket_protocol"):
            self.set_header('Sec-WebSocket-Protocol', request.sec_websocket_protocol)

        if hasattr(request, "sec_websocket_version"):
            self.set_header('Sec-WebSocket-Version', request.sec_websocket_version)
        '''
        self.set_status(101)

        self.set_response(self.websocket_wrapper())

    def calc_secure_key(self, request_key):
        try:
            magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            # 需要对请求KEY进行strip操作，否则可能会导致空格也被纳入sha1计算
            sha1 = hashlib.sha1(request_key.strip() + magic)
            key = base64.b64encode(sha1.digest())
            return key
        except Exception as e:
            return None

    def send_data(self, pData):
        pData = str(pData)
        token = "\x81"
        length = len(pData)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        return '%s%s' % (token, pData)

    def websocket_wrapper(self):
        """将普通的文件作为生成器返回"""
        yield self.make_respons_header()
        now = time.time()
        while time.time() - now < 3:
            data = self.send_data('Hello World!\r\n')
            yield data
        print('done')


class WebSocketEntry(thttpd.HttpBaseProtocol):
    def __init__(self, request):
        super(WebSocketEntry, self).__init__(request)
        if hasattr(request, "upgrade") is True:
            self.is_websocket = True
        else:
            self.is_websocket = False

    def do_get(self):
        return WebSocketRespons(self.request)

    def do_request_data(self, data):
        print(data)
