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

import time

class Message:

    generating_id = 0

    def __init__(self, key=None, remote=None, data=None, image=None):
        self.data = data
        self.wants_receipt = False
        self.timestamp = None
        self.author = None
        self.remote = None

        if key is not None:
            self.key = key

    def generateID(self):
        self.id = str(int(time.time())) + '-' + str(Message.generating_id)
        Message.generating_id += 1

    def setData(self, remote, data):
        self.remote = remote
        self.generateID()

        self.data = data
        self.timestamp = int(time.time()) * 1000
