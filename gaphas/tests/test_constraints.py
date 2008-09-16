import unittest

from gaphas.solver import Variable
from gaphas.constraint import PositionConstraint

class PositionTestCase(unittest.TestCase):
    def test_pos_constraint(self):
        """Test position constraint"""
        x1, y1 = Variable(10), Variable(11)
        x2, y2 = Variable(12), Variable(13)
        pc = PositionConstraint(origin=(x1, y1), point=(x2, y2))
        pc.solve_for()

        # origin shall remain the same
        self.assertEquals(10, x1)
        self.assertEquals(11, y1)

        # point shall be moved to origin
        self.assertEquals(10, x2)
        self.assertEquals(11, y2)

        # change just x of origin
        x1.value = 15
        pc.solve_for()
        self.assertEquals(15, x2)

        # change just y of origin
        y1.value = 14
        pc.solve_for()
        self.assertEquals(14, y2)
