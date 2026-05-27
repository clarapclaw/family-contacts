# Peaslee Family Contacts

A small, dependency-light command-line tool to manage the Peaslee family's
contacts (names, phone numbers, emails, mailing addresses, birthdays,
relationships, and notes).

- **Local source of truth:** `contacts.json` in this repo. Plain, readable JSON.
- **Human-readable mirror:** a Google Sheet titled **"Peaslee Family Contacts"**
  that you can push to with the `sync` command.

The core CLI has **no third-party dependencies** — only `sync` needs the
Google libraries.

## Requirements

- Python 3.8+
- For `sync` only: `pip install -r requirements.txt`

## Usage

Run it from the project folder. Either form works:

```bash
python3 contacts.py <command> [options]
# or
python3 -m family_contacts.cli <command> [options]
```

### Commands

| Command | What it does |
|---------|--------------|
| `add NAME [--relationship ... --phone ... --email ... --address ... --birthday ... --notes ...]` | Add a new contact |
| `list` | List everyone in a compact table |
| `search QUERY` | Search across all fields |
| `show NAME` | Show full details for one contact (name or id) |
| `update NAME [--phone ... etc.]` | Change one or more fields |
| `remove NAME [-y]` | Remove a contact (`-y` skips the confirmation) |
| `sync [--credentials PATH]` | Push all contacts to the Google Sheet |

`NAME` arguments accept a full name, a unique partial name, or the contact id.

### Examples

```bash
python3 contacts.py list
python3 contacts.py add "Grandma Peaslee" --relationship grandparent --phone +1-555-123-4567 --birthday 1955-04-02
python3 contacts.py search peaslee
python3 contacts.py show "Carl Peaslee"
python3 contacts.py update "Arthur Peaslee" --notes "Loves dinosaurs"
python3 contacts.py remove "Grandma Peaslee" -y
python3 contacts.py sync
```

The local store lives at `contacts.json`. Use `--db /path/to/file.json` to
point at a different file.

## Enabling Google Sheet sync

`sync` pushes the local contacts up to a Google Sheet so the family has a
friendly, browser-viewable copy. This needs a Google credential, which is **not**
checked into the repo (and never should be).

The tool uses a **Google service account** — a robot Google account that owns
the credential. Here is exactly what to do once:

1. Go to <https://console.cloud.google.com/> and sign in as **clara@peaslee.co**.
2. Create a project (or pick one). Name it e.g. "Family Contacts".
3. Enable two APIs for that project:
   - **Google Sheets API**
   - **Google Drive API**
   (APIs & Services → Library → search → Enable.)
4. Create a **Service Account**: APIs & Services → Credentials →
   *Create credentials* → *Service account*. Give it any name; no roles needed.
5. Open the service account → **Keys** tab → *Add key* → *Create new key* →
   **JSON**. A `.json` file downloads.
6. Put that file in this project folder and name it **`credentials.json`**
   (it is already gitignored). Or set the `GOOGLE_SHEETS_CREDENTIALS` env var to
   its path.
7. Install the Google libraries: `pip install -r requirements.txt`.
8. Run `python3 contacts.py sync`.

On the first sync the tool will **create** the sheet "Peaslee Family Contacts"
and share it with `clara@peaslee.co` as an editor. (The service account
technically owns the file; sharing lets a human open it.) Open the printed URL,
and you can also "Move" the sheet into any folder in Drive.

> Tip: the email address inside `credentials.json` (the `client_email` field) is
> the service account's address. If you'd rather sync into an *existing* sheet,
> share that sheet with that address as an Editor first.

### Columns in the sheet

`Name`, `Relationship`, `Phone`, `Email`, `Address`, `Birthday`, `Notes` — one
row per contact. The sync rewrites the sheet from the local data each time, so
**the local `contacts.json` always wins**. Edit contacts with the CLI, then
`sync`.

## Project layout

```
family-contacts/
├── contacts.py            # convenience entry point
├── contacts.json          # local data (source of truth)
├── requirements.txt       # only needed for `sync`
├── README.md
├── .gitignore             # ignores credentials.json and friends
└── family_contacts/
    ├── __init__.py
    ├── cli.py             # argument parsing + command handlers
    ├── store.py           # Contact model + JSON store (CRUD)
    └── sheet_sync.py      # Google Sheets push
```
