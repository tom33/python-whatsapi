#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading

class Signal(object):

    def __init__(self):
        self.slots = set()

    def __call__(self, *args, **kwargs):
        for slot in self.slots:
            threading.Thread(target=slot, args=args, kwargs=kwargs).start()

    def emit(self, *args, **kargs):
        self.__call__(*args, **kargs)

    def connect(self, slot):
        self.slots.add(slot)

    def disconnect(self, slot):
        self.slots.discard(Slot)

    def clear(self):
        self.slots.clear()
