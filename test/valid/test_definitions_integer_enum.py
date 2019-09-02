#!/usr/bin/env/python

import enum


class ABcd(enum.Enum):

    A = 0
    B = 1
    C = 2
    D = 3

    @staticmethod
    def from_dict(d):
        return ABcd(d)

    def as_dict(self):
        return self.value

    def __repr__(self):
        return "<Enum ABcd. {}: {}>".format(self.name, self.value)


class RootObject:
    def __init__(self):
        pass

    @staticmethod
    def from_dict(d):
        v = {}
        return RootObject(**v)

    def as_dict(self):
        d = {}
        return d

    def __repr__(self):
        return "<Class RootObject. >".format()
