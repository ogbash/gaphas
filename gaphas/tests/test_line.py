
import unittest
from gaphas.item import Line
from gaphas.canvas import Canvas
from gaphas import state


undo_list = []
redo_list = []

def undo_handler(event):
    undo_list.append(event)

def undo():
    apply_me = list(undo_list)
    del undo_list[:]
    apply_me.reverse()
    for e in apply_me:
        state.saveapply(*e)
    redo_list[:] = undo_list[:]
    del undo_list[:]



class TestCaseBase(unittest.TestCase):
    """
    Abstract test case class with undo support.
    """
    def setUp(self):
        state.observers.add(state.revert_handler)
        state.subscribers.add(undo_handler)

    def tearDown(self):
        state.observers.remove(state.revert_handler)
        state.subscribers.remove(undo_handler)



class LineTestCase(unittest.TestCase):
    """
    Basic line item tests.
    """

    def test_initial_ports(self):
        """Test initial ports amount
        """
        line = Line()
        self.assertEquals(1, len(line.ports()))


    def test_orthogonal_horizontal_undo(self):
        """
        Orthogonal line constraints bug (#107)
        """
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        assert len(canvas.solver._constraints) == 2
        after_ortho = set(canvas.solver._constraints)

        del undo_list[:]
        line.horizontal = True

        assert len(canvas.solver._constraints) == 2

        undo()

        assert not line.horizontal
        assert len(canvas.solver._constraints) == 2, canvas.solver._constraints

        line.horizontal = True

        assert line.horizontal
        assert len(canvas.solver._constraints) == 2, canvas.solver._constraints

    def test_orthogonal_line_split_segment(self):
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        assert len(canvas.solver._constraints) == 2
        after_ortho = set(canvas.solver._constraints)
        assert len(line.handles()) == 3

        del undo_list[:]

        line.split_segment(0)

        assert len(canvas.solver._constraints) == 3
        assert len(line.handles()) == 4

        undo()

        assert len(canvas.solver._constraints) == 2
        assert len(line.handles()) == 3
        assert canvas.solver._constraints == after_ortho

        line.split_segment(0)

        assert len(canvas.solver._constraints) == 3
        assert len(line.handles()) == 4
        after_split = set(canvas.solver._constraints)

        del undo_list[:]

        line.merge_segment(0)

        assert len(canvas.solver._constraints) == 2
        assert len(line.handles()) == 3

        undo()

        assert len(canvas.solver._constraints) == 3
        assert len(line.handles()) == 4
        assert canvas.solver._constraints == after_split



class LineSplitTestCase(TestCaseBase):
    """
    Tests for line splitting.
    """
    def test_split_single(self):
        """Test single line splitting
        """
        line = Line()
        line.handles()[1].pos = (20, 0)

        # we start with two handles, after split we expect 3 handles
        assert len(line.handles()) == 2

        handles = line.split_segment(0)
        handle = handles[0]
        self.assertEquals(1, len(handles))
        self.assertEquals((10, 0), handle.pos)
        self.assertEquals(3, len(line.handles()))

        # new handle is between old handles
        self.assertEquals(handle, line.handles()[1])


    def test_split_multiple(self):
        """Test multiple line splitting
        """
        line = Line()
        line.handles()[1].pos = (20, 16)
        handles = line.handles()

        # start with two handles, split into 4 parts - 3 new handles to be
        # expected
        assert len(handles) == 2

        handles = line.split_segment(0, parts=4)
        self.assertEquals(3, len(handles))
        h1, h2, h3 = handles
        self.assertEquals((5, 4), h1.pos)
        self.assertEquals((10, 8), h2.pos)
        self.assertEquals((15, 12), h3.pos)

        # new handles between old handles
        self.assertEquals(5, len(line.handles()))
        self.assertEquals(h1, line.handles()[1])
        self.assertEquals(h2, line.handles()[2])
        self.assertEquals(h3, line.handles()[3])


    def test_split_undo(self):
        """Test line splitting undo
        """
        line = Line()
        line.handles()[1].pos = (20, 0)

        # we start with two handles, after split we expect 3 handles
        assert len(line.handles()) == 2

        line.split_segment(0)
        assert len(line.handles()) == 3

        undo()

        # after undo, 2 handles are expected again
        self.assertEquals(2, len(line.handles()))


    def test_orthogonal_line_split(self):
        """Test orthogonal line splitting
        """
        assert 0

# vim:sw=4:et
