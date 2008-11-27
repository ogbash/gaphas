"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.constraint import LineAlignConstraint, LineConstraint, \
    EqualsConstraint
from gaphas.solver import Variable

class ItemConstraintTestCase(unittest.TestCase):
    """
    Item constraint creation tests. The test check functionality of
    `Item.constraint` method, not constraints themselves.
    """
    def test_line_constraint(self):
        """
        Test line creation constraint.
        """
        item = Item()
        pos = Variable(1), Variable(2)
        line = (Variable(3), Variable(4)), (Variable(5), Variable(6))
        item.constraint(pos, line=line)
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LineConstraint))
        self.assertEquals((1, 2), c._point)
        self.assertEquals(((3, 4), (5, 6)), c._line)


    def test_horizontal_constraint(self):
        """
        Test horizontal constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(p1, horizontal=p2)
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on y-axis
        self.assertEquals(2, c.a)
        self.assertEquals(4, c.b)


    def test_vertical_constraint(self):
        """
        Test vertical constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(p1, vertical=p2)
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on x-axis
        self.assertEquals(1, c.a)
        self.assertEquals(3, c.b)
