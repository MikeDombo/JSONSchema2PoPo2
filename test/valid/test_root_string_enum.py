from reprlib import repr as limitedRepr


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
        return "<Enum Abcd. {}: {}>".format(
            limitedRepr(self.name), limitedRepr(self.value)
        )
