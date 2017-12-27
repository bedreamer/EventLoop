# -*- coding: utf8 -*-
import SelectSocket
from SelectLoop import *
import struct


class CameraSampleFrame:
    """摄像头采样帧对象"""
    def __init__(self, frame):
        self.frame = frame
        self.bop = '\x05\x05\x05\x05'
        self.eop = '\x0a\x0a\x0a\x0a'
        self.payload_len = struct.unpack('>H', frame[4: 6])[0]
        self.payload_tsp = struct.unpack('>I', frame[6: 10])[0]
        self.payload_id = struct.unpack('B', frame[10])[0]
        self.payload = frame[11: 11 + self.payload_len]

    def save_bmp(self):
        """将当前数据帧保存为BMP位图"""
        pass


class TransferProtocol(SelectSocket.SelectSocketClient):
    """传输协议解析器"""
    def __init__(self, remote_host, remote_port, project_name, project_version):
        super(TransferProtocol, self).__init__(remote_host, remote_port)
        self.cache = list()
        self.frames = list()

        self.project_name = project_name
        self.project_version = project_version

    def push(self, data):
        self.cache.append(data)
        tmp_data = "".join(self.cache)

        idx_bop = tmp_data.find('\x55\x55\x55\x55')
        if idx_bop < 0:
            return

        idx_eop = tmp_data.find('\xAA\xAA\xAA\xAA')
        if idx_eop < 0:
            return

        may_frame = tmp_data[idx_bop: idx_bop + 4]

        # 提取剩余数据
        remain = tmp_data[idx_eop + 4: ]
        self.cache = [remain]

        pid = ord(may_frame[10])
        if pid == 0x01:
            frame = CameraSampleFrame(may_frame)
            # 将当前数据帧保存为BMP位图
            frame.save_bmp()
        else:
            pass

    def readable(self, fds):
        """连接上数据可读"""
        data = fds.recv(2048)
        print(len(data), data)
        self.close_connection_safely()

    def writable(self, fds):
        """连接上数据可写"""
        fds.send("GET / HTTP/1.1\r\nHost: eyehuo.com\r\n\r\n")
        loop = get_select_loop()
        loop.cancel_write(self.fds)


if __name__ == '__main__':
    loop = get_select_loop()
    t = TransferProtocol('eyehuo.com', 80, None, None)
    t.connect()
    loop.run_forever()
