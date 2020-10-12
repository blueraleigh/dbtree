import csv
import sqlite3
from .schema import schema1 as schema_init

"""
Schema for parsimony analysis of categorical character states
"""

schema1 = schema_init + """
CREATE TABLE character_states (
    id       INTEGER PRIMARY KEY,
    label    TEXT NOT NULL
);
CREATE UNIQUE INDEX character_states_label_idx ON character_states(label ASC);


CREATE TABLE character_state_data(
    otu_label         TEXT NOT NULL,
    state_label       TEXT NOT NULL
);
CREATE TRIGGER character_state_data_record_state_trig
AFTER INSERT ON character_state_data
BEGIN
    INSERT OR IGNORE INTO character_states(label) VALUES (NEW.state_label);
END;
CREATE TRIGGER character_state_data_record_state_change_trig
AFTER UPDATE OF state_label ON character_state_data
BEGIN
    INSERT OR IGNORE INTO character_states(label) VALUES (NEW.state_label);
END;
"""


def create_database(database):
    db = sqlite3.connect(database)
    db.executescript(schema1)
    db.close()


def import_chars(charfile, database):
    db = sqlite3.connect(database, isolation_level=None)
    db.execute("BEGIN")
    with open(charfile, newline='') as f:
        for otu, state in csv.reader(f):
            db.execute(
                "INSERT INTO character_state_data VALUES (?,?)", (otu, state))
    db.execute("COMMIT")
    db.close()


def import_costs(costfile, database):
    db = sqlite3.connect(database, isolation_level=None)
    db.execute("BEGIN")
    if costfile is None:
        db.execute("""
            INSERT INTO cost
            SELECT
                id, id, 0
            FROM character_states
            """
        )
        db.execute("""
            INSERT INTO cost
            SELECT
                f.id, t.id, 1
            FROM character_states AS f, character_states AS t
            WHERE f.id != t.id
            """
        )
    else:
        with open(costfile, newline='') as f:
            for frm, to, cost in csv.reader(f):
                db.execute(f"""INSERT INTO cost VALUES (
                    (SELECT id FROM character_states WHERE label='{frm}'),
                    (SELECT id FROM character_states WHERE label='{to}'),
                    {cost})""")
    db.execute("COMMIT")
    db.close()


def finalize_database(database):
    db = sqlite3.connect(database)
    db.executescript("""
        CREATE TRIGGER compute_new_costs_and_scores_trig
        AFTER UPDATE ON cost
        BEGIN
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
        END;
        UPDATE cost SET cost=0 WHERE i=1 AND j=1;
        """
    )
    db.close()
