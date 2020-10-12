"""
Schema common to sankoff parsimony analysis of continuous and
categorical characters
"""

schema1 = """
CREATE TABLE max_cost(
    max_cost     REAL DEFAULT 10000   -- large value to use for infinity
);
INSERT INTO max_cost VALUES(10000);


CREATE TABLE cost (
    i       INTEGER NOT NULL,
    j       INTEGER NOT NULL,
    cost    REAL NOT NULL CHECK (cost >= 0),
    PRIMARY KEY (i, j),
    FOREIGN KEY (i) REFERENCES character_states(id),
    FOREIGN KEY (j) REFERENCES character_states(id)
);
CREATE UNIQUE INDEX cost_ij_idx ON cost(i, j, cost);
CREATE UNIQUE INDEX cost_ji_idx ON cost(j, i, cost);


CREATE TABLE node (
    id          INTEGER NOT NULL,                    -- unique id for node
    preorder    INTEGER NOT NULL,                    -- preorder index
    postorder   INTEGER NOT NULL,                    -- postorder index
    anc         INTEGER,
    brlen       REAL,
    height      REAL,
    label       TEXT NOT NULL,
    FOREIGN KEY (anc) REFERENCES node(id)
);
CREATE INDEX node_id_idx ON node(id);
CREATE INDEX node_anc_idx ON node(anc);
CREATE UNIQUE INDEX node_preorder_idx ON node(preorder ASC);
CREATE UNIQUE INDEX node_postorder_idx ON node(postorder ASC);
CREATE INDEX node_label_idx ON node(label);
"""


schema2 = """
CREATE TEMPORARY TABLE node_state_data(node_id INTEGER, state_id INTEGER);
INSERT INTO node_state_data
SELECT
    a.id,
    (SELECT id FROM character_states WHERE label = b.state_label)
FROM
node AS a LEFT JOIN character_state_data AS b ON a.label = b.otu_label
WHERE a.preorder = a.postorder;  -- limit to leaf nodes

-- there may be multiple rows per node when state is ambiguous, hence the
-- complicated min aggregate and group by
CREATE TABLE node_state(node_id INTEGER, state TEXT);
INSERT INTO node_state
WITH
    tmp AS (
        SELECT
            a.node_id AS node_id,
            b.id AS state_id,
            min(CASE
                    WHEN a.state_id ISNULL OR a.state_id = b.id
                    THEN 0 ELSE (SELECT max_cost FROM max_cost LIMIT 1)
                END) AS cost
        FROM node_state_data AS a, character_states AS b
        GROUP BY a.node_id, b.id
)
SELECT
    node_id,
    json_group_array(cost)
FROM tmp
GROUP BY node_id
ORDER BY state_id;


CREATE TABLE downpass(
    node_id         INTEGER,
    parent_id       INTEGER,
    g               TEXT,      -- cost at node
    h               TEXT       -- cost at stem
);
CREATE INDEX downpass_node_idx ON downpass(node_id);
CREATE INDEX downpass_parent_idx ON downpass(parent_id);
CREATE INDEX downpass_covering_idx ON downpass(parent_id,node_id,h);
CREATE TRIGGER dp_insert_leaf_trig
AFTER INSERT ON downpass
WHEN NEW.g NOT NULL
BEGIN
    UPDATE downpass SET (h) = (
        WITH
        stem_cost(i, cost) AS (
            SELECT
                cost.i,
                min(cost.cost + json_each.value)
            FROM
                cost,
                json_each(NEW.g)
            WHERE cost.j = json_each.id
            GROUP BY cost.i
        )
        SELECT json_group_array(cost) FROM stem_cost ORDER BY i
    )
    WHERE rowid = NEW.rowid;
END;
CREATE TRIGGER dp_insert_node_trig
AFTER INSERT ON downpass
WHEN NEW.g IS NULL
BEGIN
    UPDATE downpass SET (g, h) = (
        WITH
        children(node_id,parent_id,h) AS (
            SELECT
                node_id,
                parent_id,
                h
            FROM downpass WHERE parent_id = NEW.node_id
        ),
        lfdesc(id, h) AS (
            SELECT
                min(node_id),
                h
            FROM children
        ),
        rtdesc(id, h) AS (
            SELECT
                max(node_id),
                h
            FROM children
        ),
        node_cost(j, cost) AS (
            SELECT
                j0.id,
                j0.value + j1.value
            FROM
                lfdesc,
                rtdesc,
                json_each(lfdesc.h) AS j0,
                json_each(rtdesc.h) AS j1
            WHERE j0.id = j1.id
        ),
        stem_cost(i, cost) AS (
            SELECT
                cost.i,
                min(cost.cost + node_cost.cost)
            FROM
                cost,
                node_cost
            WHERE cost.j = node_cost.j
            GROUP BY cost.i
        )
        VALUES(
            (SELECT json_group_array(cost) FROM node_cost ORDER BY j),
            (SELECT json_group_array(cost) FROM stem_cost ORDER BY i)
        ))
    WHERE rowid = NEW.rowid;
END;


CREATE TABLE uppass(
    node_id         INTEGER,
    parent_id       INTEGER,
    g               TEXT,       -- downpass node cost
    h               TEXT,       -- downpass stem cost
    f               TEXT        -- final uppass cost
);
CREATE INDEX uppass_node_idx ON uppass(node_id);
CREATE INDEX uppass_parent_idx ON uppass(parent_id);
CREATE TRIGGER up_insert_root_trig
AFTER INSERT ON uppass
WHEN NEW.parent_id IS NULL
BEGIN
    UPDATE uppass SET f = NEW.g WHERE rowid = NEW.rowid;
END;
CREATE TRIGGER up_insert_node_trig
AFTER INSERT ON uppass
WHEN NEW.parent_id IS NOT NULL
BEGIN
    UPDATE uppass SET (f) = (
        WITH
        final(j, cost) AS (
            SELECT
                cost.j,
                min((j0.value-j1.value) + cost.cost + j2.value)
            FROM
                cost,
                json_each(
                    (SELECT f FROM uppass WHERE node_id = NEW.parent_id)) AS j0,
                json_each(NEW.h) AS j1,
                json_each(NEW.g) AS j2
            WHERE cost.i = j0.id AND cost.i = j1.id AND cost.j = j2.id
            GROUP BY cost.j
        )
        SELECT json_group_array(cost) FROM final ORDER BY j
    )
    WHERE rowid = NEW.rowid;
END;


CREATE VIEW mpr AS
SELECT
    node_id AS node,
    g AS downpass,
    f AS uppass
FROM uppass;
"""
