#!/usr/bin/env/python

import enum


class Abcd(enum.Enum):

    A = "A"
    B = "B"
    C = "C"

    @staticmethod
    def from_dict(d):
        return Abcd(d)

    def as_dict(self):
        return self.value

    def __repr__(self):
        return "<Enum Abcd. {}: {}>".format(self.name, self.value)
