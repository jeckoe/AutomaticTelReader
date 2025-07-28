# Copilot Instructions for AutomaticTelReader

## Overview
AutomaticTelReader is a Windows desktop app for reading and archiving Telegram messages. It uses PySide6 (Qt for Python) for the GUI and Telethon for Telegram API integration. All main logic is in `AutomaticTelReader/main.py`.

## Architecture & Data Flow
- **Single-file logic**: All UI, data handling, and Telegram client logic are in `main.py`.
- **Qt Widgets/Dialogs**: The UI is built with PySide6 widgets and dialogs (e.g., login, contacts, images, messages).
- **Persistent storage**: JSON files in the project root:
	- `messages.json`: All messages (appended in real time)
	- `contacts.json`: Contacts/chats (deduplicated by ID)
	- `images.json`: Images as base64
	- `config.json`: Login credentials and config
- **Session**: Telegram session is stored in `session.session` and reused between runs.
- **No server-side/microservices**: All logic and data are local.

## Developer Workflows
- **Run the app**: `python AutomaticTelReader/main.py` (Python 3.9+, Windows)
- **Dependencies**: Install with `pip install -r AutomaticTelReader/requirements.txt` (PySide6, telethon)
- **No automated tests**: There are no test files or frameworks.
- **Debugging**: Use print statements or PySide6 dialogs. The app is single-process and event-driven.

## Project Conventions & Patterns
- **UI/UX**: All user interaction is via PySide6 dialogs/widgets. All user-facing text (errors, confirmations) is in Italian.
- **Persistence**: All data is saved/loaded as JSON with `encoding='utf-8'`. Handle missing/corrupt files gracefully (show Italian error dialogs).
- **Login**: After first login, credentials are saved in `config.json` and auto-filled on next launch.
- **Message Handling**: New messages are appended to `messages.json` and shown in the UI in real time.
- **Images**: Images are stored as base64 in `images.json` and displayed in dialogs.
- **Contacts/Chats**: Deduplicate by ID and update on new message receipt.

## Integration Points
- **Telegram**: All Telegram API access is via Telethon. The session file is reused.
- **No other external APIs**: All other data is local.

## Examples & Patterns
- To add a new persistent data type, follow the pattern in `save_message`, `save_contact`, or `save_image` in `main.py`.
- To add a new dialog, subclass `QDialog` and follow the structure of `ContactsDialog` or `ImageDialog`.
- Always update the UI and JSON data together when adding features.

## Key Files
- `AutomaticTelReader/main.py`: All logic and UI
- `AutomaticTelReader/requirements.txt`: Dependencies
- `messages.json`, `contacts.json`, `images.json`, `config.json`: Persistent data
- `session.session`: Telegram session

---

**For all changes:**
- Preserve Italian user-facing text
- Handle all errors with user-friendly dialogs (in Italian)
- Keep all persistent data in JSON and update the UI accordingly
