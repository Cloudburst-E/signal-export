"""Main script for sigexport."""

import shutil
from pathlib import Path
from typing import Optional
import os

from typer import Argument, Context, Exit, Option, colors, run, secho

from sigexport import create, data, files, logging, merge, utils
from sigexport.gcs import GCSClient

OptionalPath = Optional[Path]
OptionalStr = Optional[str]


def main(
    ctx: Context,
    dest: Path = Argument(None),
    source: OptionalPath = Option(None, help="Path to Signal source directory"),
    old: OptionalPath = Option(None, help="Path to previous export to merge"),
    password: OptionalStr = Option(None, help="Linux-only. Password to decrypt DB key"),
    chats: str = Option(
        "", help="Comma-separated chat names to include: contact names or group names"
    ),
    json_output: bool = Option(
        True, "--json/--no-json", "-j", help="Whether to create JSON output"
    ),
    list_chats: bool = Option(
        False, "--list-chats", "-l", help="List available chats and exit"
    ),
    include_empty: bool = Option(
        False, "--include-empty", help="Whether to include empty chats"
    ),
    overwrite: bool = Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite contents of output directory if it exists",
    ),
    to_gcs: bool = Option(
        False, "--to-gcs", help="Upload attachments to Google Cloud Storage"
    ),
    verbose: bool = Option(False, "--verbose", "-v"),
    _: bool = Option(False, "--version", callback=utils.version_callback),
) -> None:
    """
    Read the Signal directory and output attachments and chat to DEST directory.

    Example to list chats:

        sigexport --list-chats

    Example to export all to a directory:

        sigexport ~/outputdir
    """
    logging.verbose = verbose

    if not any((dest, list_chats)):
        secho(ctx.get_help())
        # secho("Error: Missing argument 'DEST'", fg=colors.RED)
        raise Exit(code=1)

    if source:
        source_dir = Path(source).expanduser().absolute()
    else:
        source_dir = utils.source_location()
    if not (source_dir / "config.json").is_file():
        secho(f"Error: config.json not found in directory {source_dir}")
        raise Exit(code=1)

    convos, contacts = data.fetch_data(
        source_dir,
        password=password,
        chats=chats,
        include_empty=include_empty,
    )

    if list_chats:
        names = sorted(v.name for v in contacts.values() if v.name is not None)
        secho(" | ".join(names))
        raise Exit()

    dest = Path(dest).expanduser()
    if not dest.is_dir():
        dest.mkdir(parents=True, exist_ok=True)
    elif overwrite:
        shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
    else:
        secho(
            f"Output folder '{dest}' already exists, didn't do anything!", fg=colors.RED
        )
        raise Exit()

    contacts = utils.fix_names(contacts)

    secho("Copying and renaming attachments")
    files.copy_attachments(source_dir, dest, convos, contacts, to_gcs)

    if json_output and old:
        secho(
            "Warning: currently, JSON does not support merging with the --old flag",
            fg=colors.RED,
        )

    secho("Creating output files")
    chat_dict = create.create_chats(convos, contacts)

    if old:
        secho(f"Merging old at {old} into output directory")
        secho("No existing files will be deleted or overwritten!")
        chat_dict = merge.merge_with_old(chat_dict, contacts, dest, Path(old))

    for key, messages in chat_dict.items():
        if len(messages) == 0:
            continue
        name = contacts[key].name
        # some contact names are None
        if not name:
            name = "None"
        js_path = dest / "data.json"

        js_f = js_path.open("a", encoding="utf-8")

        try:
            for msg in messages:
                print(msg.dict_str(), file=js_f)
        finally:
            js_f.close()

    if to_gcs:
        gcs_client = GCSClient()
        gcs_client.upload_message_media_file(dest / 'data.json', 'data.json', overwrite=True)
        os.remove(js_path)

    secho("Done!", fg=colors.GREEN)


def cli() -> None:
    """cli."""
    run(main)
