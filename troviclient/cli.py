from troviclient import TroviClient
import click
import yaml
import logging

from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from rocrate.model.softwareapplication import SoftwareApplication
from rocrate.model.metadata import Metadata

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], auto_envvar_prefix="TROVI")


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--keycloak_url", help="")
@click.option("--keycloak_realm", help="")
@click.option("--oidc_client_id", help="")
@click.option("--oidc_client_secret", help="")
@click.option("--admin", default=False, help="")
@click.option("--base_url", default="https://trovi.chameleoncloud.org", help="")
@click.pass_context
def cli(
    ctx,
    keycloak_url,
    keycloak_realm,
    oidc_client_id,
    oidc_client_secret,
    admin,
    base_url,
):
    ctx.ensure_object(dict)
    ctx.obj["troviclient"] = TroviClient(
        keycloak_url,
        keycloak_realm,
        oidc_client_id,
        oidc_client_secret,
        admin,
        base_url,
    )


@cli.group("tag")
def tag():
    pass


@tag.command("list", short_help="list tags")
@click.pass_context
def list_tags(ctx):
    tags = ctx.obj["troviclient"].list_tags()
    table = _make_table()
    table.add_column("Tag")
    for tag in tags:
        table.add_row(tag["tag"])
    console.print(table)


@cli.group("artifact")
def artifact():
    pass


@artifact.command("list", short_help="list artifacts")
@click.pass_context
def list_artifacts(ctx):
    artifacts = ctx.obj["troviclient"].list_artifacts()
    table = _make_table()
    table.add_column("Title")
    table.add_column("UUID", min_width=36, overflow="fold")
    table.add_column("Created")
    table.add_column("Owner")
    for artifact in artifacts:
        table.add_row(
            artifact["title"],
            artifact["uuid"],
            artifact["created_at"],
            artifact["owner_urn"][len("urn:trovi:user:"):],
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


SUPPORTED_ENVIRONEMNTS = {
    "chameleon_jupyterlab": {
        "identifier": "#ChameleonJupyterLab",
        "properties": {
            "name": "Chameleon JupyterLab",
            "url": "https://jupyter.chameleoncloud.org/",
            "trovi_type": "jupyterhub",
            "trovi_arguments": "{}",
        },
    },
}


def _artifact_environment(crate, type):
    return SoftwareApplication(crate, **SUPPORTED_ENVIRONEMNTS.get(type))


@artifact.command("generate")
@click.option("--name", required=True, help="The name of the artifact")
@click.option(
    "--short-description",
    required=True,
    help="Short one-line description of the artifact.",
)
@click.option("--description", required=True, help="Long explanation of artifact.")
@click.option(
    "--tag",
    multiple=True,
    required=True,
    help="Relevant tags. See `trovi tag list`. Can be included multiple times.",
)
@click.option(
    "--environment_type",
    default="chameleon_jupyterlab",
    type=click.Choice(SUPPORTED_ENVIRONEMNTS.keys()),
    help="Type of experiment environment this artifact runs in.",
)
@click.option(
    "--author",
    multiple=True,
    help="Author information formatted as 'name:institution'. Can be included multiple times.",
    required=True,
)
@click.option(
    "--output_file",
    default="trovi.json",
    help="File to save metadata to. Defaults to `trovi.json`",
)
@click.pass_context
def create(
    ctx,
    name,
    description,
    short_description,
    tag,
    environment_type,
    author,
    output_file,
):
    Metadata.BASENAME = output_file

    crate = ROCrate()

    crate.name = name
    crate.disambiguatingDescription = short_description
    crate.description = description
    crate.keywords = ",".join(tag)

    authors = []
    for entry in author:
        try:
            name, institution = entry.split(":", 1)
            authors.append({"name": name.strip(), "affiliation": institution.strip()})
        except ValueError:
            click.echo(
                f"Error: Invalid format for author '{entry}'. Expected 'name:institution'."
            )
            return

    crate.root_dataset["author"] = [
        crate.add(
            Person(
                crate,
                f"author_{i}",
                properties=properties,
            )
        )
        for i, properties in enumerate(authors)
    ]

    crate.root_dataset["actionApplication"] = [
        crate.add(_artifact_environment(crate, environment_type))
    ]

    crate.write("./")
