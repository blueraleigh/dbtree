class Node:
    """
    A node in a tree

    The data structure used corresponds to a polytomous tree data model.
    Each ancestor only stores a reference to its leftmost child. But
    each child stores a references to its immediate sibling on both
    the left and the right. Children thus form a doubly-linked list
    with the leftmost child as the head.
    """
    def __init__(self):
        self.anc = None     # ref to ancestor
        self.lfdesc = None  # ref to leftmost child
        self.next = None    # ref to next sibling
        self.prev = None    # ref to prev sibling
        self.index = -1     # unique identifier
        self.lfidx = -1     # index in preorder traversal
        self.rtidx = -1     # index in postorder traversal
        self.brlen = 0.0
        self.height = 0.0
        self.label = ""
        self.note = ""
        self.data = {}

    @property
    def istip(self):
        return not self.lfdesc

    def add_child(self, node):
        assert isinstance(node, Node)
        desc = self.lfdesc
        if not desc:
            self.lfdesc = node
        else:
            while desc.next:
                desc = desc.next
            desc.next = node
            node.prev = desc
        node.anc = self

    def remove_child(self, node):
        assert isinstance(node, Node)
        if node.anc == self:
            if node == self.lfdesc:
                lf = node.next
                if lf:
                    lf.prev = None
                self.lfdesc = lf
            elif not node.next:
                rt = node.prev
                rt.next = None
            else:
                lf = node.prev
                rt = node.next
                lf.next = rt
                rt.prev = lf
            node.prev = None
            node.next = None
            node.anc = None
            return node
        return None

    def swap(self, a, b):
        assert isinstance(a, Node)
        assert isinstance(b, Node)
        assert a.anc == self
        assert b.anc == self
        assert a != b
        an = a.next
        ap = a.prev
        bn = b.next
        bp = b.prev
        if a.next == b:
            b.next = a
            b.prev = a.prev
            a.next = bn
            a.prev = b
            if ap:
                ap.next = b
            if bn:
                bn.prev = a
        elif b.next == a:
            a.next = b
            a.prev = b.prev
            b.next = an
            b.prev = a
            if bp:
                bp.next = a
            if an:
                an.prev = b
        else:
            a.next = bn
            a.prev = bp
            b.next = an
            b.prev = ap
            if an:
                an.prev = b
            if ap:
                ap.next = b
            if bn:
                bn.prev = a
            if bp:
                bp.next = a
        if a == self.lfdesc:
            self.lfdesc = b
        elif b == self.lfdesc:
            self.lfdesc = a
        ai, al, ar = a.index, a.lfidx, a.rtidx
        bi, bl, br = b.index, b.lfidx, b.rtidx
        a.index, a.lfidx, a.rtidx = bi, bl, br
        b.index, b.lfidx, b.rtidx = ai, al, ar

    def rotate(self):
        kids = list(self.children())
        start = 0
        end = len(kids) - 1
        while end > start:
            self.swap(kids[start], kids[end])
            start += 1
            end -= 1

    def ladderize(self):
        for node in self.levelorder_internal():
            n = len(list(node.children()))
            while n > 1:
                new_n = 0
                c = node.lfdesc.next
                for i in range(1, n):
                    if c.prev.ntips < c.ntips:
                        node.swap(c.prev, c)
                        new_n = i
                    c = c.next
                n = new_n

    def children(self):
        desc = self.lfdesc
        while desc:
            yield desc
            desc = desc.next

    def preorder(self):
        yield self
        for child in self.children():
            for d in child.preorder():
                yield d

    def postorder(self):
        for child in self.children():
            for d in child.postorder():
                yield d
        yield self

    def levelorder(self):
        curlvl = [self]
        nxtlvl = []
        n = 1
        while n:
            for _ in range(n):
                node = curlvl.pop()
                nxtlvl.extend(node.children())
                yield node
            curlvl = nxtlvl
            nxtlvl = []
            n = len(curlvl)

    def tips(self):
        return (node for node in self.preorder() if node.istip)

    def preorder_internal(self):
        return (node for node in self.preorder() if not node.istip)

    def postorder_internal(self):
        return (node for node in self.postorder() if not node.istip)

    def levelorder_internal(self):
        return (node for node in self.levelorder() if not node.istip)

    def is_binary(self):
        if self.istip:
            return False
        return True if self.nnodes == (2*self.ntips-1) else False

    def max_height(self):
        return max(tip.height for tip in self.tips())

    @property
    def ntips(self):
        if hasattr(self, "_ntips"):
            return self._ntips
        else:
            self._ntips = len(list(self.tips()))
            return self._ntips

    @property
    def nnodes(self):
        if hasattr(self, "_nnodes"):
            return self._nnodes
        else:
            self._nnodes = len(list(self.preorder()))
            return self._nnodes

    @property
    def sql(self):
        return "INSERT INTO node VALUES ("\
            f"{self.index},{self.lfidx},{self.rtidx},"\
            f"{self.anc.index},{self.brlen},{self.height},{self.label}"\
            ");"

def mrca(a, b):
    assert isinstance(a, Node)
    assert isinstance(b, Node)
    assert a != b
    mrca = None
    path = {}
    while a:
        path.update({a: True})
        a = a.anc
    while b:
        mrca = path.get(b, None)
        if mrca:
            break
        b = b.anc
    return mrca
