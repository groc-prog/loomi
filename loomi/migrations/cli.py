import click

from loomi.migrations.actions import apply_pending_migration, generate_migration_file
from loomi.migrations.settings import MigrationSettings


@click.group()
@click.version_option(package_name="loomi")
def cli():
    """Toolkit for loomi migrations."""


@cli.command(name="create-migration")
@click.argument("name")
def create_migration(name: str):
    """
    Generate a new version-controlled migration file.
    """
    settings = MigrationSettings()

    click.echo(f"[*] Generating migration: {name}...")
    generated_file = generate_migration_file(name, settings)
    click.secho(f"OK: Created {str(generated_file)}", fg="green")


@cli.command(name="apply-migration")
def apply_migration():
    """
    Run pending migrations against the configured database.
    """
    settings = MigrationSettings()

    click.echo(f"[*] Connecting to: {settings.db_dsn}")
    click.echo("[*] Applying all pending migrations")

    applied_migrations, failed_migration = apply_pending_migration(settings)
    if failed_migration:
        click.secho(
            f"FAILURE: Migration {failed_migration} could not be applied successfully.",
            fg="red",
            bold=True,
        )
    else:
        click.secho(
            f"SUCCESS: {applied_migrations} migrations applied successfully.", fg="green", bold=True
        )


if __name__ == "__main__":
    cli()
