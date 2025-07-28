"""
AutomaticTelReader - Applicazione per il monitoraggio automatico dei messaggi Telegram

Questa applicazione permette di ricevere e salvare automaticamente tutti i messaggi
Telegram ricevuti, con supporto per immagini, contatti e gestione delle chat.

Autore: jeckoe
Versione: 1.0
"""

import sys
import os
import json
import datetime
import base64
import uuid

# Import PySide6 per l'interfaccia grafica
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QListWidget, QLineEdit, QMessageBox, 
                               QHBoxLayout, QDialog, QTextEdit, QInputDialog, 
                               QDialogButtonBox, QListView, QAbstractItemView, 
                               QListWidgetItem)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon, QFont, QPixmap, QImage

# Import Telethon per l'integrazione con Telegram
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat

# Costanti per i file di configurazione e dati
IMAGES_FILE = 'images.json'        # File per il salvataggio delle immagini (base64)
SESSION_FILE = 'session.session'   # File di sessione Telegram
MESSAGES_FILE = 'messages.json'    # File per la cronologia dei messaggi
CONFIG_FILE = 'config.json'        # File di configurazione (credenziali API)
CONTACTS_FILE = 'contacts.json'    # File per il database dei contatti

# Placeholder per le credenziali API (verranno caricate da config.json)
API_ID = ''
API_HASH = ''

class LoginWidget(QWidget):
    """
    Widget per la gestione del login e autenticazione Telegram.
    
    Questa classe gestisce l'interfaccia di login, permettendo all'utente di inserire
    le credenziali API Telegram (API ID, API Hash, numero di telefono) e salvandole
    per usi futuri in un file di configurazione.
    
    Attributes:
        on_login (callable): Callback da chiamare quando il login viene effettuato
        api_id_input (QLineEdit): Campo di input per l'API ID
        api_hash_input (QLineEdit): Campo di input per l'API Hash
        phone_input (QLineEdit): Campo di input per il numero di telefono
        login_btn (QPushButton): Pulsante per confermare il login
    """
    
    def __init__(self, on_login):
        """
        Inizializza il widget di login.
        
        Args:
            on_login (callable): Funzione callback da chiamare quando il login è completato
        """
        super().__init__()
        self.on_login = on_login
        self.setWindowTitle('Login Telegram')
        
        # Configura il layout principale
        layout = QVBoxLayout()
        
        # Crea i campi di input per le credenziali
        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText('API ID')
        
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText('API Hash')
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('Numero di telefono')
        
        # Crea il pulsante di login
        self.login_btn = QPushButton('Login')
        self.login_btn.clicked.connect(self.try_login)
        
        # Aggiunge gli elementi al layout
        layout.addWidget(QLabel('Inserisci le credenziali Telegram:'))
        layout.addWidget(self.api_id_input)
        layout.addWidget(self.api_hash_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)
        
        # Carica le credenziali salvate precedentemente, se presenti
        self.load_saved_credentials()

    def load_saved_credentials(self):
        """
        Carica le credenziali salvate dal file di configurazione.
        
        Se il file config.json esiste e contiene credenziali valide,
        riempie automaticamente i campi di input per comodità dell'utente.
        """
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Popola i campi con i dati salvati
                self.api_id_input.setText(str(data.get('api_id', '')))
                self.api_hash_input.setText(data.get('api_hash', ''))
                self.phone_input.setText(data.get('phone', ''))
            except Exception:
                # Se c'è un errore nella lettura, ignora silenziosamente
                pass

    def try_login(self):
        """
        Gestisce il tentativo di login validando i campi e salvando le credenziali.
        
        Valida che tutti i campi necessari siano compilati, salva le credenziali
        nel file di configurazione e chiama la callback di login.
        """
        # Ottiene e pulisce i valori dai campi di input
        api_id = self.api_id_input.text().strip()
        api_hash = self.api_hash_input.text().strip()
        phone = self.phone_input.text().strip()
        
        # Verifica che tutti i campi siano compilati
        if not (api_id and api_hash and phone):
            QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori!')
            return
        
        # Salva le credenziali nel file di configurazione
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'api_id': api_id, 
                'api_hash': api_hash, 
                'phone': phone
            }, f)
        
        # Chiama la callback di login con le credenziali
        self.on_login(api_id, api_hash, phone)

class MessageListener(QThread):
    """
    Thread separato per l'ascolto dei messaggi Telegram in tempo reale.
    
    Questa classe gestisce la connessione con l'API Telegram e riceve automaticamente
    tutti i nuovi messaggi, salvandoli localmente e emettendo segnali per aggiornare
    l'interfaccia utente.
    
    Signals:
        new_message (Signal): Emesso quando viene ricevuto un nuovo messaggio
    
    Attributes:
        api_id (str): ID dell'API Telegram
        api_hash (str): Hash dell'API Telegram  
        phone (str): Numero di telefono dell'utente
        client (TelegramClient): Client Telegram per la comunicazione
        start_time (str): Timestamp di inizio della sessione
    """
    
    # Segnale emesso quando arriva un nuovo messaggio
    new_message = Signal(dict)
    
    def __init__(self, api_id, api_hash, phone):
        """
        Inizializza il listener dei messaggi.
        
        Args:
            api_id (str): ID dell'API Telegram
            api_hash (str): Hash dell'API Telegram
            phone (str): Numero di telefono per l'autenticazione
        """
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        
        # Registra il timestamp di inizio per filtrare i messaggi della sessione corrente
        self.start_time = datetime.datetime.utcnow().isoformat()

    def run(self):
        """
        Metodo principale del thread che avvia il loop asincrono per Telegram.
        
        Questo metodo viene chiamato automaticamente quando il thread viene avviato.
        """
        import asyncio
        # Avvia il loop asincrono per gestire la comunicazione con Telegram
        asyncio.run(self._main())

    async def _main(self):
        """
        Metodo asincrono principale per la gestione della connessione Telegram.
        
        Configura il client Telegram, gestisce l'autenticazione e imposta
        l'handler per i nuovi messaggi.
        """
        # Crea e avvia il client Telegram
        self.client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        
        # Handler per i nuovi messaggi
        @self.client.on(events.NewMessage)
        async def handler(event):
            """
            Gestisce ogni nuovo messaggio ricevuto.
            
            Args:
                event: Evento del messaggio ricevuto da Telegram
            """
            # Ottiene informazioni sul mittente del messaggio
            sender = await event.get_sender()
            now = datetime.datetime.utcnow().isoformat()
            sender_info = self.extract_sender_info(sender)
            
            # Gestisce le informazioni della chat/gruppo se presente
            chat_info = None
            if hasattr(event, 'chat') and event.chat:
                chat_info = self.extract_sender_info(event.chat)
            
            # Gestisce le immagini allegate al messaggio
            image_id = None
            if hasattr(event.message, 'photo') and event.message.photo:
                # Scarica l'immagine in memoria e la codifica in base64
                img_bytes = await self.client.download_media(event.message.photo, file=bytes)
                if img_bytes:
                    image_id = str(uuid.uuid4())
                    self.save_image(image_id, img_bytes, now, sender_info, chat_info)
            
            # Crea l'oggetto messaggio con tutte le informazioni
            msg = {
                'from_id': str(event.sender_id),        # ID del mittente
                'text': event.raw_text,                 # Testo del messaggio
                'date': str(event.date),                # Data/ora originale del messaggio
                'received_at': now,                     # Timestamp di ricezione
                'sender': sender_info,                  # Informazioni del mittente
                'chat': chat_info if chat_info else None,  # Informazioni della chat
                'image_id': image_id                    # ID dell'immagine (se presente)
            }
            
            # Salva il messaggio e aggiorna i contatti
            self.save_message(msg)
            self.save_contact(sender_info)
            if chat_info:
                self.save_contact(chat_info)
            
            # Emette il segnale per aggiornare l'interfaccia utente
            self.new_message.emit(msg)
        
        # Mantiene la connessione attiva fino alla disconnessione
        await self.client.run_until_disconnected()

    def extract_sender_info(self, sender):
        """
        Estrae le informazioni dettagliate da un oggetto sender di Telegram.
        
        Questa funzione analizza il tipo di sender (User, Channel, Chat) e estrae
        tutte le informazioni rilevanti per la memorizzazione e visualizzazione.
        
        Args:
            sender: Oggetto sender di Telegram (User, Channel, Chat, o None)
            
        Returns:
            dict: Dizionario contenente le informazioni estratte del sender
        """
        if sender is None:
            return {'type': 'unknown'}
        
        # Inizializza il dizionario delle informazioni con l'ID
        info = {'id': str(getattr(sender, 'id', ''))}
        
        if isinstance(sender, User):
            # Gestisce gli utenti individuali
            info['type'] = 'user'
            info['first_name'] = getattr(sender, 'first_name', '')
            info['last_name'] = getattr(sender, 'last_name', '')
            info['username'] = getattr(sender, 'username', '')
            info['phone'] = getattr(sender, 'phone', '')
            info['is_self'] = getattr(sender, 'is_self', False)  # Indica se è l'utente stesso
            
        elif isinstance(sender, Channel):
            # Gestisce i canali Telegram
            info['type'] = 'channel'
            info['title'] = getattr(sender, 'title', '')
            info['username'] = getattr(sender, 'username', '')
            info['is_verified'] = getattr(sender, 'verified', False)  # Canale verificato
            info['is_scam'] = getattr(sender, 'scam', False)          # Canale segnalato come scam
            info['is_gigagroup'] = getattr(sender, 'gigagroup', False)  # Gigagruppo
            
        elif isinstance(sender, Chat):
            # Gestisce i gruppi normali
            info['type'] = 'group'
            info['title'] = getattr(sender, 'title', '')
            info['username'] = getattr(sender, 'username', '')
            info['is_megagroup'] = getattr(sender, 'megagroup', False)  # Supergruppo
            
        else:
            # Tipo di sender non riconosciuto
            info['type'] = 'unknown'
            
        return info

    def save_message(self, msg):
        """
        Salva un messaggio nel file JSON della cronologia.
        
        Aggiunge il nuovo messaggio alla lista esistente di messaggi salvati
        nel file messages.json, mantenendo la cronologia completa.
        
        Args:
            msg (dict): Dizionario contenente i dati del messaggio da salvare
        """
        messages = []
        
        # Carica i messaggi esistenti se il file esiste
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except Exception:
                # Se c'è un errore nella lettura, inizializza lista vuota
                messages = []
        
        # Aggiunge il nuovo messaggio alla lista
        messages.append(msg)
        
        # Salva la lista aggiornata nel file
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def save_contact(self, sender):
        """
        Salva o aggiorna le informazioni di un contatto nel database.
        
        Mantiene un database di tutti i contatti incontrati, aggiornando
        le informazioni esistenti o aggiungendo nuovi contatti.
        
        Args:
            sender (dict): Dizionario contenente le informazioni del contatto
        """
        contacts = {}
        
        # Carica i contatti esistenti se il file esiste
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
            except Exception:
                # Se c'è un errore nella lettura, inizializza dizionario vuoto
                contacts = {}
        
        # Ottiene l'ID del sender come stringa
        sid = str(sender.get('id', ''))
        
        if sid and sid not in contacts:
            # Nuovo contatto: aggiunge tutto il dizionario
            contacts[sid] = sender
        elif sid:
            # Contatto esistente: aggiorna le informazioni
            contacts[sid].update(sender)
        
        # Salva il database contatti aggiornato
        with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)

    def save_image(self, image_id, img_bytes, date, sender_info, chat_info):
        """
        Salva un'immagine ricevuta codificandola in base64.
        
        Le immagini vengono salvate nel file images.json come stringhe base64
        insieme ai metadati (data, mittente, chat).
        
        Args:
            image_id (str): ID univoco per l'immagine
            img_bytes (bytes): Dati binari dell'immagine
            date (str): Timestamp di ricezione
            sender_info (dict): Informazioni del mittente
            chat_info (dict): Informazioni della chat (se presente)
        """
        images = {}
        
        # Carica le immagini esistenti se il file esiste
        if os.path.exists(IMAGES_FILE):
            try:
                with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                    images = json.load(f)
            except Exception:
                # Se c'è un errore nella lettura, inizializza dizionario vuoto
                images = {}
        
        # Crea l'entry per l'immagine con tutti i metadati
        images[image_id] = {
            'base64': base64.b64encode(img_bytes).decode('utf-8'),  # Immagine codificata
            'date': date,                                           # Data di ricezione
            'sender': sender_info,                                  # Info mittente
            'chat': chat_info                                       # Info chat
        }
        
        # Salva il database immagini aggiornato
        with open(IMAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(images, f, ensure_ascii=False, indent=2)

class ContactsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Contatti Telegram')
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Segoe UI', 10))
        layout.addWidget(QLabel('Contatti salvati:'))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.load_contacts()
        self.list_widget.itemClicked.connect(self.show_contact_details)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setFont(QFont('Consolas', 9))
        layout.addWidget(QLabel('Dettagli contatto:'))
        layout.addWidget(self.details)
        close_btn = QPushButton('Chiudi')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_contacts(self):
        self.list_widget.clear()
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                for cid, info in contacts.items():
                    display = f"[{info.get('type', 'unknown')}] {info.get('title', info.get('first_name', ''))} ({cid})"
                    self.list_widget.addItem(display)
            except Exception:
                pass

    def show_contact_details(self, item):
        text = item.text()
        cid = text.split('(')[-1].rstrip(')')
        if os.path.exists(CONTACTS_FILE):
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                contacts = json.load(f)
            info = contacts.get(cid, {})
            self.details.setText(json.dumps(info, indent=2, ensure_ascii=False))

class ImageDialog(QDialog):
    def __init__(self, image_base64, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Immagine del messaggio')
        layout = QVBoxLayout()
        img_bytes = base64.b64decode(image_base64)
        image = QImage.fromData(img_bytes)
        pixmap = QPixmap.fromImage(image)
        label = QLabel()
        label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(label)
        close_btn = QPushButton('Chiudi')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)

class MessagesOfChatDialog(QDialog):
    def __init__(self, chat_id, chat_title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Messaggi di {chat_title}")
        self.setMinimumWidth(500)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(QLabel(f"Messaggi ricevuti da: {chat_title}"))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.load_messages(chat_id)
        self.list_widget.itemClicked.connect(self.show_image_if_any)
        self.image_dialog = None

    def load_messages(self, chat_id):
        self.list_widget.clear()
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            for msg in messages:
                chat = msg.get('chat') or msg.get('sender')
                if not chat or chat.get('id') != chat_id:
                    continue
                text = msg.get('text', '')
                date = msg.get('date', '')
                image_id = msg.get('image_id')
                display = f"[{date}] {text}"
                item = QListWidgetItem(display)
                if image_id:
                    item.setToolTip('Clicca per vedere l\'immagine')
                    item.setData(Qt.UserRole, image_id)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self.list_widget.addItem(item)

    def show_image_if_any(self, item):
        image_id = item.data(Qt.UserRole)
        if image_id:
            image_b64 = self.load_image_base64(image_id)
            if image_b64:
                self.image_dialog = ImageDialog(image_b64, self)
                self.image_dialog.exec()
                self.image_dialog = None

    def load_image_base64(self, image_id):
        if os.path.exists(IMAGES_FILE):
            with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                images = json.load(f)
            img = images.get(image_id)
            if img:
                return img.get('base64')
        return None

class ChatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Chat salvate')
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(QLabel('Chat da cui sono stati ricevuti messaggi:'))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.load_chats()
        self.list_widget.itemClicked.connect(self.show_messages_of_chat)

    def load_chats(self):
        self.list_widget.clear()
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            chats = {}
            for msg in messages:
                chat = msg.get('chat') or msg.get('sender')
                if not chat:
                    continue
                chat_id = chat.get('id')
                chat_title = chat.get('title') or chat.get('first_name') or chat.get('username') or chat_id
                if chat_id not in chats:
                    chats[chat_id] = {'title': chat_title}
            for cid, info in chats.items():
                item = QListWidgetItem(f"{info['title']}")
                item.setData(Qt.UserRole, cid)
                self.list_widget.addItem(item)

    def show_messages_of_chat(self, item):
        chat_id = item.data(Qt.UserRole)
        chat_title = item.text()
        dialog = MessagesOfChatDialog(chat_id, chat_title, self)
        dialog.exec()

class MessagesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Messaggi Telegram')
        self.setMinimumWidth(420)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        left_layout = QVBoxLayout()
        self.contacts_btn = QPushButton('Contatti')
        self.contacts_btn.setIcon(QIcon.fromTheme('user-group'))
        self.contacts_btn.setMinimumHeight(40)
        self.contacts_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.contacts_btn.clicked.connect(self.open_contacts)
        self.chats_btn = QPushButton('Chat')
        self.chats_btn.setIcon(QIcon.fromTheme('chat'))
        self.chats_btn.setMinimumHeight(40)
        self.chats_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.chats_btn.clicked.connect(self.open_chats)
        self.clear_btn = QPushButton('Elimina Cronologia')
        self.clear_btn.setIcon(QIcon.fromTheme('edit-delete'))
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.clear_btn.clicked.connect(self.clear_history)
        left_layout.addWidget(self.contacts_btn)
        left_layout.addWidget(self.chats_btn)
        left_layout.addWidget(self.clear_btn)
        left_layout.addStretch()
        main_layout.addLayout(left_layout)
        right_layout = QVBoxLayout()
        title = QLabel('Messaggi ricevuti:')
        title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        right_layout.addWidget(title)
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Segoe UI', 10))
        self.list_widget.setStyleSheet('QListWidget { background: #222; color: #eee; border-radius: 8px; padding: 8px; }')
        right_layout.addWidget(self.list_widget)
        self.placeholder = QLabel('Nessun messaggio ricevuto in questa sessione.')
        font_placeholder = QFont('Segoe UI', 9)
        font_placeholder.setItalic(True)
        self.placeholder.setFont(font_placeholder)
        self.placeholder.setStyleSheet('color: #888;')
        self.placeholder.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.placeholder)
        self.placeholder.hide()
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)
        self.session_start_time = None
        self.contacts_dialog = None
        self.update_placeholder()

    def set_session_start_time(self, start_time):
        self.session_start_time = start_time
        self.load_messages()

    def get_display_name(self, msg):
        sender = msg.get('sender', {})
        chat = msg.get('chat', {})
        # Preferisci il nome del gruppo/canale se presente
        if chat and chat.get('title'):
            return chat.get('title')
        # Altrimenti, se utente
        if sender.get('first_name') or sender.get('last_name'):
            return f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
        if sender.get('username'):
            return sender.get('username')
        if sender.get('title'):
            return sender.get('title')
        # Fallback: ID
        return sender.get('id', msg.get('from_id', ''))

    def load_messages(self):
        self.list_widget.clear()
        count = 0
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            for msg in messages:
                if self.session_start_time and msg.get('received_at') and msg['received_at'] >= self.session_start_time:
                    display_name = self.get_display_name(msg)
                    self.list_widget.addItem(f"Da {display_name}: {msg['text']}")
                    count += 1
        self.update_placeholder(count)

    def add_message(self, msg):
        if self.session_start_time and msg.get('received_at') and msg['received_at'] >= self.session_start_time:
            display_name = self.get_display_name(msg)
            self.list_widget.addItem(f"Da {display_name}: {msg['text']}")
        self.update_placeholder()

    def update_placeholder(self, count=None):
        if count is None:
            count = self.list_widget.count()
        self.placeholder.setVisible(count == 0)

    def open_contacts(self):
        if self.contacts_dialog is None:
            self.contacts_dialog = ContactsDialog(self)
        self.contacts_dialog.load_contacts()
        self.contacts_dialog.details.clear()
        self.contacts_dialog.exec()
        self.contacts_dialog = None

    def open_chats(self):
        dialog = ChatsDialog(self)
        dialog.exec()

    def clear_history(self):
        reply = QMessageBox.question(self, 'Conferma eliminazione',
            'Sei sicuro di voler eliminare tutta la cronologia dei messaggi e delle immagini? L\'operazione è irreversibile.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for f in [MESSAGES_FILE, IMAGES_FILE]:
                try:
                    with open(f, 'w', encoding='utf-8') as file:
                        json.dump([] if f == MESSAGES_FILE else {}, file)
                except Exception:
                    pass
            self.load_messages()
            QMessageBox.information(self, 'Cronologia eliminata', 'Tutta la cronologia è stata eliminata con successo.')

class MainApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.login_widget = LoginWidget(self.on_login)
        self.messages_widget = MessagesWidget()
        self.listener_thread = None
        self._should_quit = False
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
        self.messages_widget.closeEvent = self.on_main_window_close
        self.listener_thread.start()

    def on_main_window_close(self, event):
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.requestInterruption()
            self.listener_thread.quit()
            self.listener_thread.wait(3000)
        event.accept()
        self.quit()

if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec()) 