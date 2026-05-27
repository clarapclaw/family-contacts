"""Local data store for family contacts.

The local store is the source of truth. It is a plain JSON file so the data is
easy to read, diff, and back up. The Google Sheet is a synced mirror of this.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from typing import List, Optional

# Fields that make up a contact, in the canonical column order used everywhere
# (CLI display, JSON, and the Google Sheet).
FIELDS = ["name", "relationship", "phone", "email", "address", "birthday", "notes"]

# Human-readable column headers for the Google Sheet, aligned with FIELDS.
SHEET_HEADERS = ["Name", "Relationship", "Phone", "Email", "Address", "Birthday", "Notes"]


@dataclass
class Contact:
    """A single contact record."""

    name: str
    relationship: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    birthday: str = ""  # stored as ISO YYYY-MM-DD when known
    notes: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_row(self) -> List[str]:
        """Return the contact as a row matching SHEET_HEADERS / FIELDS order."""
        return [getattr(self, f) or "" for f in FIELDS]

    @classmethod
    def from_dict(cls, data: dict) -> "Contact":
        known = {k: data.get(k, "") for k in FIELDS}
        known["id"] = data.get("id") or uuid.uuid4().hex
        return cls(**known)


class ContactStore:
    """Loads/saves contacts from a JSON file on disk."""

    def __init__(self, path: str):
        self.path = path
        self.contacts: List[Contact] = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.contacts = [Contact.from_dict(c) for c in raw.get("contacts", [])]
        else:
            self.contacts = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        payload = {"contacts": [c.to_dict() for c in self.contacts]}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # --- CRUD -----------------------------------------------------------

    def add(self, contact: Contact) -> Contact:
        self.contacts.append(contact)
        self.save()
        return contact

    def all(self) -> List[Contact]:
        return sorted(self.contacts, key=lambda c: c.name.lower())

    def get(self, identifier: str) -> Optional[Contact]:
        """Find a contact by id (exact) or by a case-insensitive name match."""
        for c in self.contacts:
            if c.id == identifier:
                return c
        ident = identifier.lower()
        matches = [c for c in self.contacts if c.name.lower() == ident]
        if len(matches) == 1:
            return matches[0]
        # Fall back to a unique partial name match.
        partial = [c for c in self.contacts if ident in c.name.lower()]
        if len(partial) == 1:
            return partial[0]
        return None

    def search(self, query: str) -> List[Contact]:
        q = query.lower()
        results = []
        for c in self.contacts:
            haystack = " ".join(c.to_row()).lower()
            if q in haystack:
                results.append(c)
        return sorted(results, key=lambda c: c.name.lower())

    def update(self, identifier: str, changes: dict) -> Optional[Contact]:
        c = self.get(identifier)
        if not c:
            return None
        for key, value in changes.items():
            if key in FIELDS and value is not None:
                setattr(c, key, value)
        self.save()
        return c

    def remove(self, identifier: str) -> Optional[Contact]:
        c = self.get(identifier)
        if not c:
            return None
        self.contacts = [x for x in self.contacts if x.id != c.id]
        self.save()
        return c
