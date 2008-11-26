
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



class LineTestCase(TestCaseBase):
    """
    Basic line item tests.
    """

    def test_initial_ports(self):
        """Test initial ports amount
        """
        line = Line()
        self.assertEquals(1, len(line.ports()))


    def test_orthogonal_horizontal_undo(self):
        """Test orthogonal line constraints bug (#107)
        """
        canvas = Canvas()
        line = Line()
        canvas.add(line)
        assert not line.horizontal
        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        self.assertEquals(2, len(canvas.solver._constraints))
        after_ortho = set(canvas.solver._constraints)

        del undo_list[:]
        line.horizontal = True

        self.assertEquals(2, len(canvas.solver._constraints))

        undo()

        self.assertFalse(line.horizontal)
        self.assertEquals(2, len(canvas.solver._constraints))

        line.horizontal = True

        self.assertTrue(line.horizontal)
        self.assertEquals(2, len(canvas.solver._constraints))


    def test_orthogonal_line_undo(self):
        """Test orthogonal line undo
        """
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        # start with no orthogonal constraints
        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        # check orthogonal constraints
        assert len(canvas.solver._constraints) == 2
        assert len(line.handles()) == 3

        undo()

        self.assertFalse(line.orthogonal)
        self.assertEquals(0, len(canvas.solver._constraints))
        self.assertEquals(2, len(line.handles()))



class LineMergeTestCase(TestCaseBase):
    """
    Tests for line merging.
    """
    def test_merge_first_single(self):
        """Test single line merging starting from 1st segment
        """
        line = Line()
        line.handles()[1].pos = (20, 0)
        line.split_segment(0)

        # we start with 3 handles and 2 ports, after merging 2 handles and
        # 1 port are expected
        assert len(line.handles()) == 3
        assert len(line.ports()) == 2
        old_ports = line.ports()[:]

        handles, ports = line.merge_segment(0)
        # deleted handles and ports
        self.assertEquals(1, len(handles))
        self.assertEquals(2, len(ports))
        # handles and ports left after segment merging
        self.assertEquals(2, len(line.handles()))
        self.assertEquals(1, len(line.ports()))

        self.assertTrue(handles[0] not in line.handles())
        self.assertTrue(ports[0] not in line.ports())
        self.assertTrue(ports[1] not in line.ports())

        # old ports are completely removed as they are replaced by new one
        # port
        self.assertEquals(old_ports, ports)

        # finally, created port shall span between first and last handle
        port = line.ports()[0]
        self.assertEquals((0, 0), port.start)
        self.assertEquals((20, 0), port.end)


    def test_merge_multiple(self):
        """Test multiple line merge
        """
        line = Line()
        line.handles()[1].pos = (20, 16)
        line.split_segment(0, count=3)
 
        # start with 4 handles and 3 ports, merge 3 segments
        assert len(line.handles()) == 4
        assert len(line.ports()) == 3
 
        print line.handles()
        handles, ports = line.merge_segment(0, count=3)
        self.assertEquals(2, len(handles))
        self.assertEquals(3, len(ports))
        self.assertEquals(2, len(line.handles()))
        self.assertEquals(1, len(line.ports()))

        self.assertTrue(set(handles).isdisjoint(set(line.handles())))
        self.assertTrue(set(ports).isdisjoint(set(line.ports())))

        # finally, created port shall span between first and last handle
        port = line.ports()[0]
        self.assertEquals((0, 0), port.start)
        self.assertEquals((20, 16), port.end)

 
    def test_merge_undo(self):
        """Test line merging undo
        """
        line = Line()
        line.handles()[1].pos = (20, 0)

        # split for merging
        line.split_segment(0)
        assert len(line.handles()) == 3
        assert len(line.ports()) == 2

        # clear undo stack before merging
        del undo_list[:]
 
        # merge with empty undo stack
        line.merge_segment(0)
        assert len(line.handles()) == 2
        assert len(line.ports()) == 1
 
        # after merge undo, 3 handles and 2 ports are expected again
        undo()
        self.assertEquals(3, len(line.handles()))
        self.assertEquals(2, len(line.ports()))
 
 
    def test_orthogonal_line_merge(self):
        """Test orthogonal line merging
        """
        canvas = Canvas()
        line = Line()
        line.handles()[-1].pos = 100, 100
        canvas.add(line)

        # prepare the line for merging
        line.orthogonal = True
        line.split_segment(0)

        assert len(canvas.solver._constraints) == 3
        assert len(line.handles()) == 4 
        assert len(line.ports()) == 3 

        # test the merging
        line.merge_segment(0)

        self.assertEquals(2, len(canvas.solver._constraints))
        self.assertEquals(3, len(line.handles()))
        self.assertEquals(2, len(line.ports()))

 
    def test_params_errors(self):
        """Test parameter error exceptions
        """
        line = Line()
        line.split_segment(0)
        # no segment -1
        self.assertRaises(ValueError, line.merge_segment, -1)
 
        line = Line()
        line.split_segment(0)
        # no segment no 2
        self.assertRaises(ValueError, line.merge_segment, 2)
 
        line = Line()
        line.split_segment(0)
        # can't merge one or less segments :)
        self.assertRaises(ValueError, line.merge_segment, 0, 1)
 
        line = Line()
        # can't merge line with one segment
        self.assertRaises(ValueError, line.merge_segment, 0)

        line = Line()
        line.split_segment(0)
        # 2 segments: no 0 and 1. cannot merge as there are no segments
        # after segment no 1
        self.assertRaises(ValueError, line.merge_segment, 1)

        line = Line()
        line.split_segment(0)
        # 2 segments: no 0 and 1. cannot merge 3 segments as there are no 3
        # segments
        self.assertRaises(ValueError, line.merge_segment, 0, 3)


# vim:sw=4:et
