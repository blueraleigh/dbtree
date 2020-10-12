import sqlite3
from .newick import read_newick_file
from .schema import schema2


def finalize_database(database):
    db = sqlite3.connect(database)
    db.executescript(schema2)
    db.close()


def import_newick(newickfile, database):
    root = read_newick_file(newickfile)
    db = sqlite3.connect(database, isolation_level=None)
    db.execute("BEGIN")
    for node in root.preorder():
        values = (node.index, node.lfidx, node.rtidx,
                node.anc.index if node.anc else None,
                node.brlen, node.height, node.label)
        db.execute("INSERT INTO node VALUES (?,?,?,?,?,?,?)", values)
    db.execute("COMMIT")
    db.close()


def compute_parsimony_scores(database):
    db = sqlite3.connect(database)
    db.executescript("""
        DELETE FROM downpass;
        INSERT INTO downpass(node_id,parent_id,g)
        SELECT
            node.id,
            node.anc,
            node_state.state
        FROM node LEFT JOIN node_state ON node.id = node_state.node_id
        ORDER BY postorder;

        DELETE FROM uppass;
        INSERT INTO uppass(node_id,parent_id,g,h)
        SELECT
            node_id,
            parent_id,
            g,
            h
        FROM downpass JOIN node ON node_id=id
        ORDER BY preorder;
        """
    )
    db.close()

