"""
Test all the tools provided by gaphas.
"""

import unittest

from gaphas.tool import ConnectHandleTool
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Item, Element, Line
from gaphas.view import View, GtkView


class ConnectHandleToolGlueTestCase(unittest.TestCase):
    """
    Test handle connection tool glue method.
    """
    def setUp(self):
        """
        Create canvas, view and handle connection tool. A box and line are
        added to the canvas.
        """
        self.canvas = Canvas()

        self.box = Box()
        self.canvas.add(self.box)
        self.box.matrix.translate(100, 50)
        self.box.width = 40 
        self.box.height = 40 
        self.box.request_update()

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


    def test_item_and_port_glue(self):
        """Test glue operation to an item and its ports"""

        ports = self.box.ports()

        # glue to port nw-ne
        item, port = self.tool.glue(self.view, self.line, self.head, 120, 50)
        self.assertEquals(item, self.box)
        self.assertEquals(ports[0], port)

        # glue to port ne-se
        item, port = self.tool.glue(self.view, self.line, self.head, 140, 70)
        self.assertEquals(item, self.box)
        self.assertEquals(ports[1], port)

        # glue to port se-sw
        item, port = self.tool.glue(self.view, self.line, self.head, 120, 90)
        self.assertEquals(item, self.box)
        self.assertEquals(ports[2], port)

        # glue to port sw-nw
        item, port = self.tool.glue(self.view, self.line, self.head, 100, 70)
        self.assertEquals(item, self.box)
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
        assure that ConnectHandleTool._can_glue is called once (for the
        found port), it cannot be called four times (once for every port).
        """

        # count ConnectHandleTool._can_glue calls
        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0
                
            def _can_glue(self, *args):
                self._calls += 1
                return True

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, 120, 50)
        assert item and port
        self.assertEquals(1, tool._calls)


    def test_glue_cannot_glue(self):
        """Test if glue method respects ConnectHandleTool._can_glue method"""

        class Tool(ConnectHandleTool):
            def _can_glue(self, *args):
                return False

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, 120, 50)
        self.assertTrue(item is None)
        self.assertTrue(port is None)


# vim: sw=4:et:ai
