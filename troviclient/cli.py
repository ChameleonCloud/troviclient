from troviclient import TroviClient
import click
import yaml
import logging

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    auto_envvar_prefix='TROVI'
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--keycloak_url", required=True, help="")
@click.option("--keycloak_realm", required=True, help="")
@click.option("--oidc_client_id", required=True, help="")
@click.option("--oidc_client_secret", required=True, help="")
@click.option("--admin", required=True, help="")
@click.option("--base_url", required=True, help="")
@click.pass_context
def cli(ctx, keycloak_url, keycloak_realm, oidc_client_id, oidc_client_secret, admin, base_url):
    ctx.ensure_object(dict)
    ctx.obj["troviclient"] = TroviClient(
        keycloak_url, keycloak_realm,
        oidc_client_id, oidc_client_secret,
        admin, base_url
    )


@cli.group("artifact")
def artifact():
    pass


@artifact.command("list", short_help="list artifacts")
@click.pass_context
def list_artifacts(ctx):
    artifacts = ctx.obj["troviclient"].list_artifacts()
    table = _make_table()
    table.add_column("Title")
    table.add_column("UUID")
    table.add_column("Created")
    table.add_column("Owner")
    table.add_column("Visibility")
    for artifact in artifacts:
        table.add_row(
            artifact["title"],
            artifact["uuid"],
            artifact["created_at"],
            artifact["owner_urn"][len("urn:trovi:user:"):],
            artifact["visibility"],
        )
    console.print(table)


@artifact.command("show", short_help="list artifacts")
@click.argument("uuid")
@click.pass_context
def show_artifact(ctx, uuid):
    artifact = ctx.obj["troviclient"].get_artifact(uuid)
    table = _make_table()
    table.add_column("Property")
    table.add_column("Value")
    for prop, value in artifact.items():
        table.add_row(prop, _format_value(value))
    console.print(table)


def _format_value(value):
    if isinstance(value, dict) or isinstance(value, list):
        return yaml.dump(value).strip()
    return value


def _make_table(*headers, **kwargs):
    kwargs.setdefault("show_header", True)
    kwargs.setdefault("header_style", "bold green")
    kwargs.setdefault("box", box.MINIMAL_HEAVY_HEAD)
    return Table(*headers, **kwargs)
