# troviclient

`troviclient` is a Python library that can help you interact with the
[Trovi API](https://github.com/chameleoncloud/trovi) for sharing and
storing experimental artifacts.

[troviclient] also includes a command-line interface (CLI) that can be used
for interacting with the Trovi API.

## Installation

You can install this library via pip from git

```shell
pip install git+https://github.com/ChameleonCloud/troviclient.git
```

## Usage

### `trovi artifact list`

Shows a table list of public artifacts, displaying name, uuid, created date, and author.

### `trovi artifact show UUID`

Shows all metadata for a given artifact.

Parameters:
- `UUID` - The UUID of the artifact to show

### `trovi artifact generate`

Generate a `trovi.json` RO-crate file with artifact metadata. This file is required to import an artifact directly from GitHub, and it must be present in the root of the repository.

Parameters:

- `--name` - The artifact's title
- `--short-description` - A (<80 character) description of the artifact
- `--description` - A full description fo the artifact, which may contain Markdown text
- `--tag` - A tag for this artifact (see `trovi tag list`). Can be included multiple times.
- `--author` - A string representing an author of this artifact formatted as "REAL NAME:INSTITUTION". Can be included multiple times.

### `trovi tag list`

Lists all supported tags on trovi.