import os
import click
from .database import (
    import_newick,
    finalize_database,
    compute_parsimony_scores
)

from .sankoff import (
    create_database as sankoff_create_database,
    import_chars as sankoff_import_chars,
    import_costs as sankoff_import_costs,
    finalize_database as sankoff_finalize_database,
)

from .tdalp import (
    create_database as tdalp_create_database,
    import_chars as tdalp_import_chars,
    import_costs as tdalp_import_costs,
    finalize_database as tdalp_finalize_database,
)


@click.group()
def cli():
    pass

@cli.command()
@click.option("-treefile", required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Newick format phylogeny.")
@click.option("-charfile", required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Character state data.")
@click.option("-costfile", type=click.Path(exists=True, dir_okay=False),
    help="State-to-state transition cost matrix.")
@click.argument("database", type=click.Path(exists=False, dir_okay=False))
def sankoff(treefile, charfile, costfile, database):
    if os.path.exists(database):
        click.UsageError("database already exists.")
    sankoff_create_database(database)
    import_newick(treefile, database)
    sankoff_import_chars(charfile, database)
    sankoff_import_costs(costfile, database)
    finalize_database(database)
    sankoff_finalize_database(database)


@cli.command()
@click.option("-treefile", required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Newick format phylogeny.")
@click.option("-charfile", required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Character state data.")
@click.option("-nbreaks", type=int, default=4,
    help="Cut continuous character values into this number of groups.",
    show_default=True)
@click.option("-brksfile", type=click.Path(exists=True, dir_okay=False),
    help="User-supplied breaks for cutting character values.")
@click.option("-asymmetry", type=float, default=1, help="Asymmetry parameter.")
@click.argument("database", type=click.Path(exists=False, dir_okay=False))
def tdalp(treefile, charfile, nbreaks, brksfile, asymmetry, database):
    if os.path.exists(database):
        click.UsageError("database already exists.")
    tdalp_create_database(database)
    import_newick(treefile, database)
    try:
        tdalp_import_costs(brksfile, nbreaks, asymmetry, charfile, database)
    except Exception as err:
        click.UsageError(str(err))
    tdalp_import_chars(charfile, database)
    finalize_database(database)
    tdalp_finalize_database(database)
