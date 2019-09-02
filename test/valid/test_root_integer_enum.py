#!/usr/bin/env/python

import enum


class Abcd(enum.Enum):

    A = 0
    B = 1
    C = 2
    D = 3

    @staticmethod
    def from_dict(d):
        return Abcd(d)

    def as_dict(self):
        return self.value

    def __repr__(self):
        return "<Enum Abcd. {}: {}>".format(self.name, self.value)
