import unittest

from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Line
from gaphas.constraint import BalanceConstraint, EqualsConstraint

class ConstraintProjectionTestCase(unittest.TestCase):
    def test_line_projection(self):
        """Test projection with line's handle on element's side"""
        line = Line()
        line.matrix.translate(15, 50)
        h1, h2 = line.handles()
        h1.x, h1.y = 0, 0
        h2.x, h2.y = 20, 20

        box = Box()
        box.matrix.translate(10, 10)
        box.width = 40
        box.height = 20
        h_nw, h_ne, h_se, h_sw = box.handles()


        canvas = Canvas()
        canvas.add(line)
        canvas.add(box)

        # move line's second handle on box side
        h2.x, h2.y = 5, -20

        bc = BalanceConstraint(band=(h_sw.x, h_se.x), v=h2.x, balance=0.25)
        canvas.proj(bc, x={h_sw.x: box, h_se.x: box, h2.x: line})
        canvas._solver.add_constraint(bc)

        eq = EqualsConstraint(a=h_se.y, b=h2.y)
        canvas.proj(eq, y={h_se.y: box, h2.y: line})
        canvas._solver.add_constraint(eq)

        box.request_update()
        line.request_update()

        canvas.update()

        box.width = 60
        box.height = 30

        canvas.update()

        # expect h2.x to be moved due to balance constraint
        self.assertEquals(10, h2.x)
        self.assertEquals(-10, h2.y)
