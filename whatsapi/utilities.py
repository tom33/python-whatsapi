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

import hashlib
import string

def encodeString(string):
    res = []
    for char in string:
        res.append(ord(char))
    return res

def str_base(number, radix):
    """str_base( number, radix ) -- reverse function to int(str,radix) and long(str,radix)"""

    if not 2 <= radix <= 36:
        raise ValueError, 'radix must be in 2..36'

    abc = string.digits + string.letters

    result = ''

    if number < 0:
        number = -number
        sign = '-'
    else:
        sign = ''

    while True:
        (number, rdigit) = divmod(number, radix)
        result = abc[rdigit] + result
        if number == 0:
            return sign + result

class ByteArray:

    def __init__(self, size=0):
        self.size = size
        self.buf = bytearray(size)

    def toByteArray(self):
        res = ByteArray()
        for b in self.buf:
            res.buf.append(b)

        return res

    def reset(self):
        self.buf = bytearray(self.size)

    def getBuffer(self):
        return self.buf

    def read(self):
        return self.buf.pop(0)

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
            b[off + count] = self.read()
            count = count + 1

        return count

    def write(self, data):
        if type(data) is int:
            self.writeInt(data)
        elif type(data) is chr:
            self.buf.append(ord(data))
        elif type(data) is str:
            self.writeString(data)
        elif type(data) is bytearray:
            self.writeByteArray(data)
        else:
            raise Exception('Unsupported datatype ' + str(type(data)))

    def writeByteArray(self, b):
        for i in b:
            self.buf.append(i)

    def writeInt(self, integer):
        self.buf.append(integer)

    def writeString(self, string):
        for c in string:
            self.writeChar(c)

    def writeChar(self, char):
        self.buf.append(ord(char))


class S40MD5Digest:
    def __init__(self):
        self.m = hashlib.md5()

    def update(self, string):
        self.m.update(str(string))

    def reset(self):
        self.m = hashlib.md5()

    def digest(self):
        res = self.m.digest()
        resArr = bytearray(res)

        return resArr

