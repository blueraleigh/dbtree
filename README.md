# Installation

Create a virtual environment in the top-level dbtree directory

```
cd dbtree
python3 -m venv venv
source venv/bin/activate
```

Then use pip to install dbtree in that environment

```
pip3 install -e .
```

This installs the command line program `dbtree`. Type `dbtree --help` to see
the list of commands. Type `dbtree CMD --help` to see the help for a specific
command.

# Examples

The following performs a simple parsimony analysis of squamate reproductive
mode

```
dbtree sankoff -treefile data/squamatatree.tre -charfile data/reprod.csv reprod.db
```

To query the results we use the `sqlite3` CLI to the database

```
sqlite3 reprod.db

SELECT * FROM character_states; -- examine the character states
SELECT * FROM cost;             -- examine state-to-state transition costs
SELECT * FROM mpr;              -- examine node states

-- Let's assume it's twice as costly to evolve oviparity from viviparity 
-- than the reverse
UPDATE cost SET cost=2 WHERE i=2 AND j=1;

-- Then we can re-examine the node states to see if any inferences have changed
SELECT * FROM mpr;              
```

The `mpr` table holds the maximum parsimony reconstructions. It is a three
column table: the first column is the node id; second column, downpass cost;
third column, uppass cost. The downpass and uppass costs are stored as JSON
arrays. Each item in the array holds the minimum downpass or uppass cost that
can be achieved by setting a node's state equal to the character state with
the same index as the index in the JSON array.

The following performs a linear parsimony analysis of the logarithm of 
squamate body masses binned into 10 categories.

```
dbtree tdalp -treefile data/squamatatree.tre -charfile data/mass.csv -nbreaks 10 mass.db
```

To query the results we again use the `sqlite3` CLI to the database

```
sqlite3 mass.db

SELECT * FROM character_states; -- examine the character states
SELECT * FROM cost;             -- examine state-to-state transition costs
SELECT * FROM mpr;              -- examine node states

-- Let's assume there is a positive trend toward the evolution of large body
-- size. To do so we don't update the cost matrix directly, but rather the
-- asymmetry parameter.
UPDATE asymmetry SET l=2;

-- Then we can re-examine the node states to see if any inferences have changed
SELECT * FROM mpr;

-- If we wanted to assume the opposite, we would set the asymmetry parameter to
-- a value less than 1 instead.
UPDATE asymmetry SET l=0.5;

-- And the MPR results are again automatically updated.
SELECT * FROM mpr;
```

When you are done working with the dbtree CLI type `deactivate` in the shell.
