from .node import Node

class Newick:
    def __init__(self, newick):
        if newick[-1] != ';':
            raise Exception("missing terminating semi-colon")
        self.newick = newick
        self.nchar = len(newick)

    def read_brlen(self, cursor):
        c = self.newick[cursor]
        if (c == ":"):
            brlen = ""
            cursor += 1
            c = self.newick[cursor]
            while c != "," and c != ")" and c != ";" and cursor < self.nchar:
                brlen += c
                cursor += 1
                c = self.newick[cursor]
            try:
                brlen = float(brlen)
            except:
                raise Exception(f"invalid branch length: {brlen}")
            return (cursor, brlen)
        return (cursor, 0.0)

    def read_note(self, cursor):
        note = ""
        c = self.newick[cursor]
        if c == "[":
            cursor += 1
            c = self.newick[cursor]
            while c != "]":
                note += c
                cursor += 1
                if cursor == self.nchar:
                    break
                c = self.newick[cursor]
            if c != "]":
                raise Exception("missing closing ']' in note")
            cursor += 1
        return (cursor, note)

    def read_label(self, cursor):
        label = ""
        stopchars = [":", ",", ")", "[", ";"]
        errorchars = ["(", "["]
        c = self.newick[cursor]
        while c not in stopchars and cursor < self.nchar:
            label += c
            cursor += 1
            c = self.newick[cursor]
            if c.isspace() or c in errorchars:
                raise Exception(f"invalid character in node label: \"{c}\"")
        return (cursor, label)

    @staticmethod
    def parse(newick_string):
        parser = Newick(newick_string)
        cursor = 0
        stack = 0
        p = Node()
        c = parser.newick[cursor]
        while c != ';':
            if c == "(":
                q = Node()
                p.add_child(q)
                p = q
                stack += 1
            elif c == ",":
                q = Node()
                p.anc.add_child(q)
                p = q
            elif c == ")":
                p = p.anc
                if not p:
                    raise Exception(
                        "invalid Newick string: unmatched closing parenthesis")
                stack -= 1
            else:
                cursor, label = parser.read_label(cursor)
                cursor, note = parser.read_note(cursor)
                cursor, brlen = parser.read_brlen(cursor)
                p.label = label
                p.note = note
                p.brlen = brlen
                cursor -= 1
            cursor += 1
            c = parser.newick[cursor]
        # p is now back at the root
        if stack != 0:
            raise Exception(
                "invalid Newick string: unmatched opening parenthesis")
        for i, tip in enumerate(p.tips()):
            tip.index = i + 1
        ntip = i + 1
        for i, node in enumerate(p.preorder_internal()):
            h = node.anc.height if node.anc else 0.0
            node.index = i + ntip + 1
            node.height = h + node.brlen
        for tip in p.tips():
            tip.height = tip.anc.height + tip.brlen
        root = p
        idx = 1
        while p:
            p.lfidx = idx
            if p.istip:
                p.rtidx = idx
            idx += 1
            if p.lfdesc:
                p = p.lfdesc
            elif p.next:
                p = p.next
            else:
                # on entry p is a terminal node that marks clade boundary
                p = p.anc
                while p.anc and not p.next:
                    p.rtidx = idx
                    p = p.anc
                    idx += 1
                p.rtidx = idx
                idx += 1
                p = p.next
        return root

def read_newick_string(newick_string):
    return Newick.parse(newick_string.strip())

def read_newick_file(newick_file):
    with open(newick_file) as f:
        return Newick.parse(f.read().strip())

