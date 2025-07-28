# Copilot Instructions for AutomaticTelReader

## Overview
This project is a desktop application for reading and archiving Telegram messages, built with PySide6 (Qt for Python) for the GUI and Telethon for Telegram API integration. The main logic is in `AutomaticTelReader/main.py`.

## Architecture & Data Flow
- **main.py**: Contains all UI, data handling, and Telegram client logic. The app is structured around Qt Widgets and Dialogs for login, message viewing, contacts, and images.
- **Data files**: JSON files in the root directory (`messages.json`, `contacts.json`, `images.json`, `config.json`) are used for persistent storage. Each file has a clear schema (see code for details).
- **Session**: Telegram session is stored in `session.session`.
- **No external microservices**: All logic is local, no server-side components.

## Developer Workflows
- **Run the app**: `python AutomaticTelReader/main.py` (Python 3.9+, Windows tested)
- **Dependencies**: Managed via `requirements.txt` (PySide6, telethon)
- **No tests**: There are currently no automated tests or test framework in the repo.
- **Debugging**: Use print statements or PySide6 dialogs for debugging. The app is single-process, event-driven.

## Project Conventions & Patterns
- **UI/UX**: All user interaction is via PySide6 dialogs and widgets. Error messages and confirmations are always shown in Italian.
- **Persistence**: All data is saved/loaded as JSON. Always use `encoding='utf-8'` and handle missing/corrupt files gracefully.
- **Login**: Credentials are saved in `config.json` after first login. The app auto-fills these fields on next launch.
- **Message Handling**: New messages are appended to `messages.json` and shown in the UI in real time.
- **Images**: Images are stored as base64 in `images.json` and shown in dialogs when requested.
- **Contacts/Chats**: Contacts and chats are deduplicated by ID and updated on new message receipt.

## Integration Points
- **Telegram**: Uses Telethon for all Telegram API access. The session file is reused between runs.
- **No other external APIs**: All other data is local.

## Examples
- To add a new persistent data type, follow the pattern in `save_message`, `save_contact`, or `save_image` methods.
- To add a new dialog, subclass `QDialog` and follow the structure of `ContactsDialog` or `ImageDialog`.

## Key Files
- `AutomaticTelReader/main.py`: All logic/UI
- `requirements.txt`: Dependencies
- `*.json`: Data files (see above)

---

For any changes, preserve Italian user-facing text and handle all errors with user-friendly dialogs. If adding new features, keep all persistent data in JSON and update the UI accordingly.
