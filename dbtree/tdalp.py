import csv
import sqlite3
from math import inf as INF
from .schema import schema1 as schema_init

"""
Schema for parsimony analysis of continuous character states.
"""


schema1 = schema_init + """
CREATE TABLE asymmetry (
    l  REAL DEFAULT 1 CHECK (l > 0)
);
INSERT INTO asymmetry VALUES (1);
CREATE TRIGGER asym_disallow_insert_trig
BEFORE INSERT ON asymmetry
BEGIN
    SELECT RAISE (ABORT, 'inserts are disallowed');
END;
CREATE TRIGGER asym_disallow_delete_trig
BEFORE DELETE ON asymmetry
BEGIN
    SELECT RAISE (ABORT, 'deletes are disallowed');
END;


CREATE TABLE character_states (
    id       INTEGER PRIMARY KEY,
    mn       REAL NOT NULL,
    mx       REAL NOT NULL,
    label    TEXT GENERATED ALWAYS AS ('['||mn||','||mx||')') STORED,
    value    REAL GENERATED ALWAYS AS ((mn + mx) / 2.0) STORED
);
CREATE UNIQUE INDEX character_states_label_idx ON character_states(label ASC);
CREATE INDEX character_states_val_idx ON character_states(mn, mx, label);


CREATE TABLE character_state_data(
    otu_label         TEXT NOT NULL,
    state_value       REAL NOT NULL,
    state_label       TEXT
);
CREATE TRIGGER character_state_data_bin_trig
AFTER INSERT ON character_state_data
BEGIN
    UPDATE character_state_data SET state_label = (
        SELECT
            label
        FROM
            character_states
        WHERE
            NEW.state_value >= mn AND NEW.state_value < mx
    )
    WHERE rowid=NEW.rowid;
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
                "INSERT INTO character_state_data(otu_label,state_value) VALUES (?,?)", (otu, state))
    db.execute("COMMIT")
    db.close()


def import_costs(brksfile, nbreaks, asymmetry, charfile, database):
    db = sqlite3.connect(database, isolation_level=None)
    db.execute("BEGIN")
    MN = INF
    MX = -INF
    with open(charfile) as f:
        for otu, state in csv.reader(f):
            state = float(state)
            if state < MN:
                MN = state
            if state > MX:
                MX = state
    if brksfile is None:
        MN -= 1e-4 * (MX - MN)
        MX += 1e-4 * (MX - MN)
        step = (MX - MN) / nbreaks
        mn = MN
        for i in range(nbreaks):
            db.execute(
                "INSERT INTO character_states(mn,mx) VALUES (?,?)", (mn,mn+step))
            mn += step
    else:
        with open(brksfile) as f:
            brks = []
            for line in f:
                brks.append(float(line.strip()))
        if len(brks) % 2 != 0:
            raise Exception('invalid number of breaks')
        if max(brks) <= MX or min(brks) > MN:
            raise Exception('breaks do not span range of values')
        brks = zip(brks[:len(brks)], brks[1:])
        for mn, mx in brks:
            db.execute(
                "INSERT INTO character_states(mn,mx) VALUES (?,?)", (mn,mx))
    db.execute("UPDATE asymmetry SET l = ?", (asymmetry,))
    db.execute("COMMIT")
    db.close()

def finalize_database(database):
    db = sqlite3.connect(database)
    db.executescript("""
        CREATE TRIGGER asym_compute_new_costs_and_scores_trig
        AFTER UPDATE ON asymmetry
        BEGIN
            DELETE FROM cost WHERE i != j;
            INSERT INTO cost
            SELECT
                f.id,
                t.id,
                CASE
                    WHEN f.value < t.value
                    THEN (NEW.l) * (t.value - f.value)
                    ELSE (f.value - t.value)
                END
            FROM character_states AS f, character_states AS t
            WHERE f.id != t.id;
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
        UPDATE asymmetry SET l = (
            SELECT l FROM asymmetry
        );
        """
    )
    db.close()
