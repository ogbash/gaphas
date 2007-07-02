"""
Simple example items.
These items are used in various tests.
"""

__version__ = "$Revision$"
# $HeadURL$

from item import Handle, Element, Item
from item import NW, NE,SW, SE
from solver import solvable
import tool
from constraint import BalanceConstraint, LessThanConstraint, EqualsConstraint
from geometry import point_on_rectangle, distance_rectangle_point
from util import text_extents, text_align, text_multiline, path_ellipse

class Box(Element):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Box, self).__init__(width, height)

    def draw(self, context):
        #print 'Box.draw', self
        c = context.cairo
        nw = self._handles[NW]
        c.rectangle(0, 0, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(.8,.8,1, .8)
        else:
            c.set_source_rgba(1,1,1, .8)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()
        context.draw_children()

    def glue(self, item, handle, x, y):
        """
        Special glue method used by the ConnectingHandleTool to find
        a connection point.
        """
        h = self._handles
        hnw = h[NW]
        hse = h[SE]
        x0, y0 = float(hnw.x), float(hnw.y)
        x1, y1 = float(hse.x), float(hse.y)
        r = (x0, y0, x1 - x0, y1 - y0)
        por = point_on_rectangle(r, (x, y), border=True)
        p = distance_rectangle_point(r, (x, y))
        return p, por


class Text(Item):
    """
    Simple item showing some text on the canvas.
    """

    def __init__(self, text=None, plain=False, multiline=False, align_x=1, align_y=-1):
        super(Text, self).__init__()
        self.text = text is None and 'Hello' or text
        self.plain = plain
        self.multiline = multiline
        self.align_x = align_x
        self.align_y = align_y

    def draw(self, context):
        #print 'Text.draw', self
        cr = context.cairo
        if self.multiline:
            text_multiline(cr, 0, 0, self.text)
        elif self.plain:
            cr.show_text(self.text)
        else:
            text_align(cr, 0, 0, self.text, self.align_x, self.align_y)
        context.draw_children()

    def point(self, x, y):
        return 0


class FatLine(Item):
    def __init__(self):
        super(FatLine, self).__init__()
        self._handles.extend((Handle(), Handle()))


    def _set_height(self, height):
        h1, h2 = self._handles
        return h2.y + height


    def _get_height(self):
        h1, h2 = self._handles
        return h2.y - h1.y


    height = property(_get_height, _set_height)


    def setup_canvas(self):
        super(FatLine, self).setup_canvas()
        h1, h2 = self._handles
        h2.x = h1.x
        add = self.canvas.solver.add_constraint
        self._c1 = EqualsConstraint(a=h1.x, b=h2.x)
        self._c2 = LessThanConstraint(smaller=h1.y, bigger=h2.y, delta=20)
        add(self._c1)
        add(self._c2)


    def draw(self, context):
        cr = context.cairo
        cr.set_line_width(10)
        cr.move_to(0, 0)
        cr.line_to(0, self.height)
        cr.stroke()



class Circle(Item):
    def __init__(self):
        super(Circle, self).__init__()
        self._handles.extend((Handle(), Handle()))


    def _set_radius(self, height):
        h1, h2 = self._handles
        return h1.y + height


    def _get_radius(self):
        h1, h2 = self._handles
        return ((h2.x - h1.x) ** 2 + (h2.y - h1.y) ** 2) ** 0.5


    radius = property(_get_radius, _set_radius)


    def _get_pos(self):
        h1, h2 = self._handles
        x, y = h2.x - h1.x, h2.y - h1.y
        if x > 0:
            x = 0
        if y > 0:
            y = 0
        return abs(x), abs(y)


    pos = property(_get_pos)


    def setup_canvas(self):
        super(Circle, self).setup_canvas()
        h1, h2 = self._handles
        h1.movable = False


    def draw(self, context):
        cr = context.cairo
        x, y = self.pos
        path_ellipse(cr, x, y, 2 * self.radius, 2 * self.radius)
        cr.stroke()


class ConnectingHandleTool(tool.HandleTool):
    """
    This is a HandleTool which supports a simple connection algorithm,
    using BalanceConstraint.
    """

    def glue(self, view, item, handle, wx, wy):
        """
        It allows the tool to glue to a Box or (other) Line item.
        The distance from the item to the handle is determined in canvas
        coordinates, using a 10 pixel glue distance.
        """
        if not handle.connectable:
            return

        # Make glue distance depend on the zoom ratio (should be about 10 pixels)
        glue_distance, dummy = view.transform_distance_c2w(10, 0)
        glue_point = None
        glue_item = None
        for i in view.canvas.get_all_items():
            if not i is item:
                #ix, iy = matrix_w2i(i).transform_point(wx, wy)
                ix, iy = wx, wy
                try:
                    distance, point = i.glue(item, handle, ix, iy)
                    # Transform distance to world coordinates
                    #distance, dumy = matrix_i2w(i).transform_distance(distance, 0)
                    if distance <= glue_distance:
                        glue_distance = distance
                        glue_point = point
                        glue_item = i
                except AttributeError:
                    pass
        if glue_point:
            x, y = glue_point
            handle.x, handle.y = glue_point
        return glue_item

    def connect(self, view, item, handle, wx, wy):
        """
        Connect a handle to another item.

        In this "method" the following assumptios are made:
         1. The only item that accepts handle connections are the Box instances
         2. The only items with connectable handles are Line's
         
        """
        def side(handle, glued):
            handles = glued.handles()
            hx, hy = handle.x, handle.y
            ax, ay = handles[NW].x, handles[NW].y
            bx, by = handles[SE].x, handles[SE].y
            if abs(hx - ax) < 0.01:
                return handles[NW], handles[SW]
            elif abs(hy - ay) < 0.01:
                return handles[NW], handles[NE]
            elif abs(hx - bx) < 0.01:
                return handles[NE], handles[SE]
            else:
                return handles[SW], handles[SE]
            assert False


        def handle_disconnect():
            try:
                view.canvas.solver.remove_constraint(handle._c1)
                view.canvas.solver.remove_constraint(handle._c2)
            except KeyError:
                pass # constraint was alreasy removed
            handle._connect_constraint = None
            handle.connected_to = None
            # Remove disconnect handler:
            handle.disconnect = lambda: 0

        #print 'Handle.connect', view, item, handle, wx, wy
        glue_item = self.glue(view, item, handle, wx, wy)
        if glue_item and glue_item is handle.connected_to:
            try:
                view.canvas.solver.remove_constraint(handle._c1)
                view.canvas.solver.remove_constraint(handle._c2)
            except KeyError:
                pass # constraint was already removed


            h1, h2 = side(handle, glue_item)
            handle._c1 = BalanceConstraint(band=(h1.x, h1.x), v=handle.x)
            handle._c2 = BalanceConstraint(band=(h2.y, h2.y), v=handle.y)
            view.canvas.solver.add_constraint(handle._c1)
            view.canvas.solver.add_constraint(handle._c2)
            handle.disconnect = handle_disconnect
            return

        # drop old connetion
        if handle.connected_to:
            handle.disconnect()

        if glue_item:
            if isinstance(glue_item, Box):
                h1, h2 = side(handle, glue_item)

                # Make a constraint that keeps into account item coordinates.
                handle._c1 = BalanceConstraint(band=(h1.x, h2.x), v=handle.x)
                handle._c2 = BalanceConstraint(band=(h1.y, h2.y), v=handle.y)
                view.canvas.solver.add_constraint(handle._c1)
                view.canvas.solver.add_constraint(handle._c2)

                handle.connected_to = glue_item
                handle.disconnect = handle_disconnect

    def disconnect(self, view, item, handle):
        if handle.connected_to:
            #print 'Handle.disconnect', view, item, handle
            view.canvas.solver.remove_constraint(handle._c1)
            view.canvas.solver.remove_constraint(handle._c2)


def DefaultExampleTool():
    """
    The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
    chain = tool.ToolChain()
    chain.append(tool.HoverTool())
    chain.append(ConnectingHandleTool())
    chain.append(tool.ItemTool())
    chain.append(tool.TextEditTool())
    chain.append(tool.RubberbandTool())
    return chain


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
