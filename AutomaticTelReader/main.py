import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QLineEdit, QMessageBox
from PySide6.QtCore import QThread, Signal
from telethon import TelegramClient, events
import os
import json
import datetime
from telethon.tl.types import User, Channel, Chat

API_ID = ''
API_HASH = ''
SESSION_FILE = 'session.session'
MESSAGES_FILE = 'messages.json'
CONFIG_FILE = 'config.json'
CONTACTS_FILE = 'contacts.json'

class LoginWidget(QWidget):
    def __init__(self, on_login):
        super().__init__()
        self.on_login = on_login
        self.setWindowTitle('Login Telegram')
        layout = QVBoxLayout()
        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText('API ID')
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText('API Hash')
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('Numero di telefono')
        self.login_btn = QPushButton('Login')
        self.login_btn.clicked.connect(self.try_login)
        layout.addWidget(QLabel('Inserisci le credenziali Telegram:'))
        layout.addWidget(self.api_id_input)
        layout.addWidget(self.api_hash_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)
        self.load_saved_credentials()

    def load_saved_credentials(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.api_id_input.setText(str(data.get('api_id', '')))
                self.api_hash_input.setText(data.get('api_hash', ''))
                self.phone_input.setText(data.get('phone', ''))
            except Exception:
                pass

    def try_login(self):
        api_id = self.api_id_input.text().strip()
        api_hash = self.api_hash_input.text().strip()
        phone = self.phone_input.text().strip()
        if not (api_id and api_hash and phone):
            QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori!')
            return
        # Salva le credenziali
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'api_id': api_id, 'api_hash': api_hash, 'phone': phone}, f)
        self.on_login(api_id, api_hash, phone)

class MessageListener(QThread):
    new_message = Signal(dict)
    def __init__(self, api_id, api_hash, phone):
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.start_time = datetime.datetime.utcnow().isoformat()

    def run(self):
        import asyncio
        asyncio.run(self._main())

    async def _main(self):
        self.client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        @self.client.on(events.NewMessage)
        async def handler(event):
            sender = await event.get_sender()
            now = datetime.datetime.utcnow().isoformat()
            sender_info = self.extract_sender_info(sender)
            msg = {
                'from_id': str(event.sender_id),
                'text': event.raw_text,
                'date': str(event.date),
                'received_at': now,
                'sender': sender_info
            }
            self.save_message(msg)
            self.save_contact(sender_info)
            self.new_message.emit(msg)
        await self.client.run_until_disconnected()

    def extract_sender_info(self, sender):
        if sender is None:
            return {'type': 'unknown'}
        info = {'id': str(getattr(sender, 'id', ''))}
        if isinstance(sender, User):
            info['type'] = 'user'
            info['first_name'] = getattr(sender, 'first_name', '')
            info['last_name'] = getattr(sender, 'last_name', '')
            info['username'] = getattr(sender, 'username', '')
            info['phone'] = getattr(sender, 'phone', '')
            info['is_self'] = getattr(sender, 'is_self', False)
        elif isinstance(sender, Channel):
            info['type'] = 'channel'
            info['title'] = getattr(sender, 'title', '')
            info['username'] = getattr(sender, 'username', '')
            info['is_verified'] = getattr(sender, 'verified', False)
            info['is_scam'] = getattr(sender, 'scam', False)
            info['is_gigagroup'] = getattr(sender, 'gigagroup', False)
        elif isinstance(sender, Chat):
            info['type'] = 'group'
            info['title'] = getattr(sender, 'title', '')
            info['username'] = getattr(sender, 'username', '')
            info['is_megagroup'] = getattr(sender, 'megagroup', False)
        else:
            info['type'] = 'unknown'
        return info

    def save_message(self, msg):
        messages = []
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except Exception:
                messages = []
        messages.append(msg)
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def save_contact(self, sender):
        contacts = {}
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
            except Exception:
                contacts = {}
        sid = str(sender.get('id', ''))
        if sid and sid not in contacts:
            contacts[sid] = sender
        elif sid:
            contacts[sid].update(sender)
        with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)

class MessagesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Messaggi Telegram')
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(QLabel('Messaggi ricevuti:'))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.session_start_time = None

    def set_session_start_time(self, start_time):
        self.session_start_time = start_time

    def load_messages(self):
        self.list_widget.clear()
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            for msg in messages:
                # Mostra solo i messaggi ricevuti dopo l'avvio del watcher
                if self.session_start_time and msg.get('received_at') and msg['received_at'] >= self.session_start_time:
                    self.list_widget.addItem(f"Da {msg['from_id']}: {msg['text']}")

    def add_message(self, msg):
        # Mostra solo i messaggi ricevuti dopo l'avvio del watcher
        if self.session_start_time and msg.get('received_at') and msg['received_at'] >= self.session_start_time:
            self.list_widget.addItem(f"Da {msg['from_id']}: {msg['text']}")

class MainApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.login_widget = LoginWidget(self.on_login)
        self.messages_widget = MessagesWidget()
        self.listener_thread = None
        # Carica credenziali se esistono
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                api_id = str(data.get('api_id', ''))
                api_hash = data.get('api_hash', '')
                phone = data.get('phone', '')
                if api_id and api_hash and phone:
                    self.on_login(api_id, api_hash, phone)
                else:
                    self.login_widget.show()
            except Exception:
                self.login_widget.show()
        else:
            self.login_widget.show()

    def on_login(self, api_id, api_hash, phone):
        self.login_widget.hide()
        self.messages_widget.show()
        self.listener_thread = MessageListener(api_id, api_hash, phone)
        self.messages_widget.set_session_start_time(self.listener_thread.start_time)
        self.listener_thread.new_message.connect(self.messages_widget.add_message)
        self.listener_thread.start()

if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec()) 