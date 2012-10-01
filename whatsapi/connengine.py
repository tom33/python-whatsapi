#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2012, Tarek Galal <tarek@wazapp.im>
Modified by Bouke van der Bijl <boukevanderbijl@gmail.com>

This file is part of Wazapp, an IM application for Meego Harmattan platform that
allows communication with Whatsapp users

Wazapp is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 2 of the License, or (at your option) any later
version.

Wazapp is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Wazapp. If not, see http://www.gnu.org/licenses/.
'''

import socket
import sys

from whatsapi.exceptions import *

class MySocketConnection(socket.socket):

    def __init__(self):
        self.readSize = 1
        self.buf = []
        self.maxBufRead = 0
        self.connected = 0

        super(MySocketConnection, self).__init__(socket.AF_INET,
                socket.SOCK_STREAM)

    def flush(self):
        self.write()

    def getBuffer(self):
        return self.buffer

    def writeArray(self, data):
        for d in data:
            self.buffer.append(d)
            count_sent = self.send(chr(d))
            self.buffer = self.buffer

    def writeBuffer(self):
        for item in self.buffer:
            count_sent = self.send(chr(d))

    def reset(self):
        self.buffer = ''

    def write(self, data):
        if not self.connected:
            return

        if type(data) is int:
            self.sendall(chr(data))
        else:
            tmp = ''

            for d in data:
                tmp += chr(d)
            self.sendall(tmp)

    def setReadSize(self, size):
        self.readSize = size

    def read(self, socketOnly=0):
        x = self.recv(self.readSize)

        if len(x) == 1:
            return ord(x)
        else:
            raise ConnectionClosedException('Got 0 bytes, connection closed')

    def read2(
        self,
        b,
        off,
        length,
        ):
        '''reads into a buffer'''

        if off < 0 or length < 0 or off + length > len(b):
            raise Exception('Out of bounds')

        if length == 0:
            return 0

        if b is None:
            raise Exception('XNull pointerX')

        count = 0

        while count < length:
            b[off + count] = self.read(0)
            count = count + 1

        return count
