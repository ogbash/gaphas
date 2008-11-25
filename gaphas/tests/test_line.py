
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

        # we start with two handles and one port, after split 3 handles are
        # expected and 2 ports
        assert len(line.handles()) == 2
        assert len(line.ports()) == 1

        old_port = line.ports()[0]

        handles, ports = line.split_segment(0)
        handle = handles[0]
        self.assertEquals(1, len(handles))
        self.assertEquals((10, 0), handle.pos)
        self.assertEquals(3, len(line.handles()))
        self.assertEquals(2, len(line.ports()))

        # new handle is between old handles
        self.assertEquals(handle, line.handles()[1])
        # and old port is deleted
        self.assertTrue(old_port not in line.ports())

        # check ports order
        p1, p2 = line.ports()
        h1, h2, h3 = line.handles()
        self.assertEquals(h1.pos, p1.start)
        self.assertEquals(h2.pos, p1.end)
        self.assertEquals(h2.pos, p2.start)
        self.assertEquals(h3.pos, p2.end)


    def test_split_multiple(self):
        """Test multiple line splitting
        """
        line = Line()
        line.handles()[1].pos = (20, 16)
        handles = line.handles()
        old_ports = line.ports()[:]

        # start with two handles, split into 4 segments - 3 new handles to
        # be expected
        assert len(handles) == 2
        assert len(old_ports) == 1

        handles, ports = line.split_segment(0, count=4)
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

        self.assertEquals(4, len(line.ports()))

        # and old port is deleted
        self.assertTrue(old_ports[0] not in line.ports())

        # check ports order
        p1, p2, p3, p4 = line.ports()
        h1, h2, h3, h4, h5 = line.handles()
        self.assertEquals(h1.pos, p1.start)
        self.assertEquals(h2.pos, p1.end)
        self.assertEquals(h2.pos, p2.start)
        self.assertEquals(h3.pos, p2.end)
        self.assertEquals(h3.pos, p3.start)
        self.assertEquals(h4.pos, p3.end)
        self.assertEquals(h4.pos, p4.start)
        self.assertEquals(h5.pos, p4.end)


    def test_ports_after_split(self):
        """Test ports removal after split
        """
        line = Line()
        line.handles()[1].pos = (20, 16)

        line.split_segment(0)
        handles = line.handles()
        old_ports = line.ports()[:]

        # start with 3 handles and two ports
        assert len(handles) == 3
        assert len(old_ports) == 2

        # do split of first segment again
        # first port should be deleted, but 2nd one should remain untouched
        line.split_segment(0)
        self.assertFalse(old_ports[0] in line.ports())
        self.assertEquals(old_ports[1], line.ports()[2])


    def test_split_undo(self):
        """Test line splitting undo
        """
        line = Line()
        line.handles()[1].pos = (20, 0)

        # we start with two handles and one port, after split 3 handles and
        # 2 ports are expected
        assert len(line.handles()) == 2
        assert len(line.ports()) == 1

        line.split_segment(0)
        assert len(line.handles()) == 3
        assert len(line.ports()) == 2

        # after undo, 2 handles and 1 port are expected again
        undo()
        self.assertEquals(2, len(line.handles()))
        self.assertEquals(1, len(line.ports()))


    def test_orthogonal_line_split(self):
        """Test orthogonal line splitting
        """
        assert 0


    def test_params_errors(self):
        """Test parameter error exceptions
        """
        # there is only 1 segment
        line = Line()
        self.assertRaises(ValueError, line.split_segment, -1)

        line = Line()
        self.assertRaises(ValueError, line.split_segment, 1)

        line = Line()
        # can't split into one or less segment :)
        self.assertRaises(ValueError, line.split_segment, 0, 1)



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
        assert 0
 
 
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
