"""Command-line interface for the Peaslee family contacts manager."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List

from .store import FIELDS, Contact, ContactStore

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contacts.json"
)


# --- formatting helpers -------------------------------------------------


def _print_contact(c: Contact) -> None:
    print(f"  {c.name}")
    label_width = max(len(f) for f in FIELDS)
    for f in FIELDS:
        value = getattr(c, f)
        if value:
            print(f"    {f.capitalize():<{label_width}} : {value}")
    print(f"    {'id':<{label_width}} : {c.id}")


def _print_table(contacts: List[Contact]) -> None:
    if not contacts:
        print("No contacts found.")
        return
    name_w = max([len(c.name) for c in contacts] + [4])
    rel_w = max([len(c.relationship) for c in contacts] + [12])
    print(f"{'NAME':<{name_w}}  {'RELATIONSHIP':<{rel_w}}  PHONE / EMAIL")
    print(f"{'-' * name_w}  {'-' * rel_w}  {'-' * 20}")
    for c in contacts:
        contact_bits = " ".join(b for b in [c.phone, c.email] if b) or "-"
        print(f"{c.name:<{name_w}}  {c.relationship:<{rel_w}}  {contact_bits}")


# --- command handlers ---------------------------------------------------


def cmd_add(store: ContactStore, args) -> int:
    contact = Contact(
        name=args.name,
        relationship=args.relationship or "",
        phone=args.phone or "",
        email=args.email or "",
        address=args.address or "",
        birthday=args.birthday or "",
        notes=args.notes or "",
    )
    store.add(contact)
    print("Added contact:")
    _print_contact(contact)
    return 0


def cmd_list(store: ContactStore, args) -> int:
    _print_table(store.all())
    return 0


def cmd_search(store: ContactStore, args) -> int:
    results = store.search(args.query)
    _print_table(results)
    return 0


def cmd_show(store: ContactStore, args) -> int:
    c = store.get(args.identifier)
    if not c:
        print(f"No unique contact matching '{args.identifier}'.", file=sys.stderr)
        return 1
    _print_contact(c)
    return 0


def cmd_update(store: ContactStore, args) -> int:
    changes = {f: getattr(args, f) for f in FIELDS if getattr(args, f) is not None}
    if not changes:
        print("Nothing to update. Provide at least one field to change.", file=sys.stderr)
        return 1
    c = store.update(args.identifier, changes)
    if not c:
        print(f"No unique contact matching '{args.identifier}'.", file=sys.stderr)
        return 1
    print("Updated contact:")
    _print_contact(c)
    return 0


def cmd_remove(store: ContactStore, args) -> int:
    c = store.get(args.identifier)
    if not c:
        print(f"No unique contact matching '{args.identifier}'.", file=sys.stderr)
        return 1
    if not args.yes:
        answer = input(f"Remove '{c.name}'? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return 0
    store.remove(c.id)
    print(f"Removed '{c.name}'.")
    return 0


def cmd_sync(store: ContactStore, args) -> int:
    from . import sheet_sync

    try:
        url = sheet_sync.push(store.all(), credentials_path=args.credentials)
    except sheet_sync.SyncError as exc:
        print("Sync could not run:\n", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Synced {len(store.all())} contacts to '{sheet_sync.SHEET_TITLE}'.")
    print(f"Sheet URL: {url}")
    return 0


# --- argument parsing ---------------------------------------------------


def _add_field_options(parser: argparse.ArgumentParser, include_name: bool) -> None:
    if include_name:
        parser.add_argument("--name", help="Full name")
    parser.add_argument("--relationship", help="e.g. spouse/parent, child, friend")
    parser.add_argument("--phone", help="Phone number")
    parser.add_argument("--email", help="Email address")
    parser.add_argument("--address", help="Mailing address")
    parser.add_argument("--birthday", help="Birthday, ideally YYYY-MM-DD")
    parser.add_argument("--notes", help="Free-form notes")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contacts",
        description="Manage the Peaslee family contacts and sync them to Google Sheets.",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help="Path to the local contacts JSON store (default: contacts.json in repo).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new contact")
    p_add.add_argument("name", help="Full name")
    _add_field_options(p_add, include_name=False)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all contacts")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search contacts across all fields")
    p_search.add_argument("query", help="Text to search for")
    p_search.set_defaults(func=cmd_search)

    p_show = sub.add_parser("show", help="Show full details for one contact")
    p_show.add_argument("identifier", help="Name (or id) of the contact")
    p_show.set_defaults(func=cmd_show)

    p_update = sub.add_parser("update", help="Update fields on a contact")
    p_update.add_argument("identifier", help="Name (or id) of the contact")
    _add_field_options(p_update, include_name=True)
    p_update.set_defaults(func=cmd_update)

    p_remove = sub.add_parser("remove", help="Remove a contact")
    p_remove.add_argument("identifier", help="Name (or id) of the contact")
    p_remove.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p_remove.set_defaults(func=cmd_remove)

    p_sync = sub.add_parser("sync", help="Push local contacts to the Google Sheet")
    p_sync.add_argument(
        "--credentials", help="Path to Google service account JSON (optional)."
    )
    p_sync.set_defaults(func=cmd_sync)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = ContactStore(args.db)
    return args.func(store, args)


if __name__ == "__main__":
    sys.exit(main())
