"""
Test all the tools provided by gaphas.
"""

import unittest

from gaphas.tool import ConnectHandleTool
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Item, Element, Line
from gaphas.view import View, GtkView
from gaphas.constraint import LineConstraint

def simple_canvas(self):
    """
    This decorator adds view, canvas and handle connection tool to a test
    case. Two boxes and a line are added to the canvas as well.
    """
    self.canvas = Canvas()

    self.box1 = Box()
    self.canvas.add(self.box1)
    self.box1.matrix.translate(100, 50)
    self.box1.width = 40 
    self.box1.height = 40 
    self.box1.request_update()

    self.box2 = Box()
    self.canvas.add(self.box2)
    self.box2.matrix.translate(100, 150)
    self.box2.width = 50 
    self.box2.height = 50 
    self.box2.request_update()

    self.line = Line()
    self.head = self.line.handles()[0]
    self.canvas.add(self.line)

    self.canvas.update_now()
    self.view = GtkView()
    self.view.canvas = self.canvas
    import gtk
    win = gtk.Window()
    win.add(self.view)
    self.view.show()
    self.view.update()
    win.show()

    self.tool = ConnectHandleTool()


class ConnectHandleToolGlueTestCase(unittest.TestCase):
    """
    Test handle connection tool glue method.
    """

    def setUp(self):
        simple_canvas(self)


    def test_item_and_port_glue(self):
        """Test glue operation to an item and its ports"""

        ports = self.box1.ports()

        # glue to port nw-ne
        item, port = self.tool.glue(self.view, self.line, self.head, 120, 50)
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[0], port)

        # glue to port ne-se
        item, port = self.tool.glue(self.view, self.line, self.head, 140, 70)
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[1], port)

        # glue to port se-sw
        item, port = self.tool.glue(self.view, self.line, self.head, 120, 90)
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[2], port)

        # glue to port sw-nw
        item, port = self.tool.glue(self.view, self.line, self.head, 100, 70)
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[3], port)
        

    def test_failed_glue(self):
        """Test glue from too far distance"""
        item, port = self.tool.glue(self.view, self.line, self.head, 90, 50)
        self.assertTrue(item is None)
        self.assertTrue(port is None)


    def test_glue_call_can_glue_once(self):
        """Test if glue method calls can glue once only

        Box has 4 ports. Every port is examined once per
        ConnectHandleTool.glue method call. The purpose of this test is to
        assure that ConnectHandleTool.can_glue is called once (for the
        found port), it cannot be called four times (once for every port).
        """

        # count ConnectHandleTool.can_glue calls
        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0
                
            def can_glue(self, *args):
                self._calls += 1
                return True

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, 120, 50)
        assert item and port
        self.assertEquals(1, tool._calls)


    def test_glue_cannot_glue(self):
        """Test if glue method respects ConnectHandleTool.can_glue method"""

        class Tool(ConnectHandleTool):
            def can_glue(self, *args):
                return False

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, 120, 50)
        self.assertTrue(item is None)
        self.assertTrue(port is None)


    def test_glue_no_port_no_can_glue(self):
        """Test if glue method does not call ConnectHandleTool.can_glue method when port is not found"""

        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0

            def can_glue(self, *args):
                self._calls += 1

        tool = Tool()
        # at 300, 50 there should be no item
        item, port = tool.glue(self.view, self.line, self.head, 300, 50)
        assert item is None and port is None
        self.assertEquals(0, tool._calls)



class ConnectHandleToolConnectTestCase(unittest.TestCase):

    def setUp(self):
        simple_canvas(self)


    def _get_line(self):
        line = Line()
        head = self.line.handles()[0]
        self.canvas.add(line)
        return line, head


    def test_connect(self):
        """Test connection to an item"""
        line, head = self._get_line()
        connected = self.tool.connect(self.view, line, head, 120, 50)
        self.assertTrue(connected)
        self.assertEquals(self.box1, head.connected_to)
        self.assertTrue(head.connection_data is not None)
        self.assertTrue(isinstance(head.connection_data, LineConstraint))
        self.assertTrue(head.disconnect is not None)

        line, head = self._get_line()
        glue_item, port = self.tool.connect(self.view, line, head, 90, 50)
        self.assertTrue(glue_item is None)
        self.assertTrue(port is None)


    def test_disconnect(self):
        """Test disconnection from an item"""
        line, head = self._get_line()
        connected = self.tool.connect(self.view, line, head, 120, 50)
        assert connected

        self.tool.disconnect(self.view, line, head)
        self.assertTrue(head.connected_to is None)
        self.assertTrue(head.connection_data is None)


    def test_reconnect_another(self):
        """Test reconnection to another item"""
        line, head = self._get_line()
        connected = self.tool.connect(self.view, line, head, 120, 50)
        assert connected
        item = head.connected_to
        constraint = head.connection_data

        assert item == self.box1
        assert item != self.box2

        # connect to box2, handle's connected item and connection data
        # should differ
        connected = self.tool.connect(self.view, line, head, 120, 150)
        assert connected
        self.assertEqual(self.box2, head.connected_to)
        self.assertNotEqual(item, head.connected_to)
        self.assertNotEqual(constraint, head.connection_data)


    def test_reconnect_same(self):
        """Test reconnection to same item"""
        line, head = self._get_line()
        connected = self.tool.connect(self.view, line, head, 120, 50)
        assert connected
        item = head.connected_to
        constraint = head.connection_data

        assert item == self.box1
        assert item != self.box2

        # connect to box1 again, handle's connected item should be the same
        # but connection constraint will differ
        connected = self.tool.connect(self.view, line, head, 120, 50)
        assert connected
        self.assertEqual(self.box1, head.connected_to)
        self.assertNotEqual(constraint, head.connection_data)



# vim: sw=4:et:ai
