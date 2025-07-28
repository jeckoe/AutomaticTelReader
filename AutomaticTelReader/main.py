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
    """
    Dialog per la visualizzazione e gestione dei contatti salvati.
    
    Questa finestra di dialogo mostra tutti i contatti che sono stati salvati
    durante l'uso dell'applicazione, permettendo di visualizzare i dettagli
    di ogni contatto in formato JSON leggibile.
    
    Attributes:
        list_widget (QListWidget): Lista dei contatti disponibili
        details (QTextEdit): Area di testo per mostrare i dettagli del contatto selezionato
    """
    
    def __init__(self, parent=None):
        """
        Inizializza il dialog dei contatti.
        
        Args:
            parent (QWidget, optional): Widget parent per il dialog
        """
        super().__init__(parent)
        self.setWindowTitle('Contatti Telegram')
        self.setMinimumWidth(400)
        
        # Configura il layout principale
        layout = QVBoxLayout()
        
        # Lista dei contatti
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Segoe UI', 10))
        
        layout.addWidget(QLabel('Contatti salvati:'))
        layout.addWidget(self.list_widget)
        
        # Area per i dettagli del contatto selezionato
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setFont(QFont('Consolas', 9))  # Font monospace per JSON
        
        layout.addWidget(QLabel('Dettagli contatto:'))
        layout.addWidget(self.details)
        
        # Pulsante per chiudere il dialog
        close_btn = QPushButton('Chiudi')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Carica i contatti e imposta l'handler per la selezione
        self.load_contacts()
        self.list_widget.itemClicked.connect(self.show_contact_details)

    def load_contacts(self):
        """
        Carica e visualizza tutti i contatti salvati nel file contacts.json.
        
        Legge il file dei contatti e popola la lista con informazioni
        leggibili per ogni contatto (tipo, nome, ID).
        """
        self.list_widget.clear()
        
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                
                # Itera sui contatti e crea le voci della lista
                for cid, info in contacts.items():
                    # Determina il nome da visualizzare in base al tipo di contatto
                    display_name = (info.get('title') or 
                                  info.get('first_name', '') or 
                                  info.get('username', '') or 
                                  'Sconosciuto')
                    
                    # Crea il testo da visualizzare nella lista
                    display = f"[{info.get('type', 'unknown')}] {display_name} ({cid})"
                    self.list_widget.addItem(display)
                    
            except Exception:
                # Se c'è un errore nella lettura, ignora silenziosamente
                pass

    def show_contact_details(self, item):
        """
        Mostra i dettagli completi del contatto selezionato.
        
        Estrae l'ID del contatto dal testo dell'item selezionato
        e mostra tutti i dettagli in formato JSON nell'area di testo.
        
        Args:
            item (QListWidgetItem): Item della lista selezionato
        """
        # Estrae l'ID del contatto dal testo (tra parentesi alla fine)
        text = item.text()
        cid = text.split('(')[-1].rstrip(')')
        
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                
                # Ottiene le informazioni del contatto selezionato
                info = contacts.get(cid, {})
                
                # Mostra i dettagli in formato JSON formattato
                self.details.setText(json.dumps(info, indent=2, ensure_ascii=False))
                
            except Exception:
                self.details.setText("Errore nel caricamento dei dettagli del contatto.")

class ImageDialog(QDialog):
    """
    Dialog per la visualizzazione delle immagini ricevute tramite Telegram.
    
    Questa finestra di dialogo decodifica e mostra le immagini salvate
    in formato base64, ridimensionandole per una visualizzazione ottimale.
    
    Attributes:
        image_base64 (str): Stringa base64 dell'immagine da visualizzare
    """
    
    def __init__(self, image_base64, parent=None):
        """
        Inizializza il dialog per la visualizzazione dell'immagine.
        
        Args:
            image_base64 (str): Immagine codificata in base64 da visualizzare
            parent (QWidget, optional): Widget parent per il dialog
        """
        super().__init__(parent)
        self.setWindowTitle('Immagine del messaggio')
        
        layout = QVBoxLayout()
        
        # Decodifica l'immagine da base64 e la converte in QPixmap
        try:
            img_bytes = base64.b64decode(image_base64)
            image = QImage.fromData(img_bytes)
            pixmap = QPixmap.fromImage(image)
            
            # Crea il label per mostrare l'immagine
            label = QLabel()
            # Ridimensiona l'immagine mantenendo le proporzioni (max 400x400)
            label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(label)
            
        except Exception as e:
            # In caso di errore nella decodifica, mostra un messaggio di errore
            error_label = QLabel(f"Errore nel caricamento dell'immagine: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
        
        # Pulsante per chiudere il dialog
        close_btn = QPushButton('Chiudi')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class MessagesOfChatDialog(QDialog):
    """
    Dialog per visualizzare tutti i messaggi di una specifica chat/contatto.
    
    Questa finestra mostra cronologicamente tutti i messaggi ricevuti da
    una particolare chat, gruppo o contatto, con supporto per visualizzare
    le immagini associate ai messaggi.
    
    Attributes:
        chat_id (str): ID della chat di cui visualizzare i messaggi
        chat_title (str): Titolo/nome della chat
        list_widget (QListWidget): Lista dei messaggi della chat
        image_dialog (ImageDialog): Dialog per visualizzare le immagini (se presente)
    """
    
    def __init__(self, chat_id, chat_title, parent=None):
        """
        Inizializza il dialog dei messaggi per una specifica chat.
        
        Args:
            chat_id (str): ID univoco della chat
            chat_title (str): Nome/titolo da mostrare per la chat
            parent (QWidget, optional): Widget parent per il dialog
        """
        super().__init__(parent)
        self.setWindowTitle(f"Messaggi di {chat_title}")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Lista per i messaggi della chat
        self.list_widget = QListWidget()
        
        layout.addWidget(QLabel(f"Messaggi ricevuti da: {chat_title}"))
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
        
        # Carica i messaggi per questa chat specifica
        self.load_messages(chat_id)
        
        # Imposta l'handler per il click sui messaggi (per visualizzare immagini)
        self.list_widget.itemClicked.connect(self.show_image_if_any)
        self.image_dialog = None

    def load_messages(self, chat_id):
        """
        Carica tutti i messaggi per la chat specificata.
        
        Filtra tutti i messaggi salvati per mostrare solo quelli
        appartenenti alla chat richiesta, evidenziando quali
        contengono immagini.
        
        Args:
            chat_id (str): ID della chat di cui caricare i messaggi
        """
        self.list_widget.clear()
        
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                
                # Filtra i messaggi per questa specifica chat
                for msg in messages:
                    # Ottiene le info della chat dal messaggio (chat o sender)
                    chat = msg.get('chat') or msg.get('sender')
                    
                    # Salta i messaggi che non appartengono a questa chat
                    if not chat or chat.get('id') != chat_id:
                        continue
                    
                    # Estrae le informazioni del messaggio
                    text = msg.get('text', '')
                    date = msg.get('date', '')
                    image_id = msg.get('image_id')
                    
                    # Crea il testo da visualizzare nella lista
                    display = f"[{date}] {text}"
                    item = QListWidgetItem(display)
                    
                    # Se il messaggio ha un'immagine, lo rende cliccabile
                    if image_id:
                        item.setToolTip('Clicca per vedere l\'immagine')
                        item.setData(Qt.UserRole, image_id)
                    else:
                        # Disabilita l'item se non ha immagini
                        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    
                    self.list_widget.addItem(item)
                    
            except Exception:
                # In caso di errore, non mostra messaggi
                pass

    def show_image_if_any(self, item):
        """
        Mostra l'immagine associata al messaggio selezionato, se presente.
        
        Verifica se il messaggio selezionato ha un'immagine associata
        e la visualizza in un dialog separato.
        
        Args:
            item (QListWidgetItem): Item del messaggio selezionato
        """
        # Ottiene l'ID dell'immagine dai dati dell'item
        image_id = item.data(Qt.UserRole)
        
        if image_id:
            # Carica l'immagine dal database
            image_b64 = self.load_image_base64(image_id)
            
            if image_b64:
                # Mostra l'immagine in un dialog dedicato
                self.image_dialog = ImageDialog(image_b64, self)
                self.image_dialog.exec()
                self.image_dialog = None

    def load_image_base64(self, image_id):
        """
        Carica i dati base64 di un'immagine dal database.
        
        Args:
            image_id (str): ID univoco dell'immagine da caricare
            
        Returns:
            str: Stringa base64 dell'immagine, o None se non trovata
        """
        if os.path.exists(IMAGES_FILE):
            try:
                with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                    images = json.load(f)
                
                # Ottiene i dati dell'immagine
                img = images.get(image_id)
                if img:
                    return img.get('base64')
                    
            except Exception:
                # In caso di errore, restituisce None
                pass
                
        return None

class ChatsDialog(QDialog):
    """
    Dialog per visualizzare tutte le chat da cui sono stati ricevuti messaggi.
    
    Questa finestra analizza tutti i messaggi salvati e crea una lista
    delle chat/contatti unici, permettendo di aprire la cronologia completa
    di messaggi per ciascuna chat.
    
    Attributes:
        list_widget (QListWidget): Lista delle chat disponibili
    """
    
    def __init__(self, parent=None):
        """
        Inizializza il dialog delle chat.
        
        Args:
            parent (QWidget, optional): Widget parent per il dialog
        """
        super().__init__(parent)
        self.setWindowTitle('Chat salvate')
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Lista delle chat
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        layout.addWidget(QLabel('Chat da cui sono stati ricevuti messaggi:'))
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
        
        # Carica le chat disponibili e imposta l'handler per la selezione
        self.load_chats()
        self.list_widget.itemClicked.connect(self.show_messages_of_chat)

    def load_chats(self):
        """
        Carica e visualizza tutte le chat uniche da cui sono stati ricevuti messaggi.
        
        Analizza tutti i messaggi salvati per estrarre le chat uniche,
        creando una lista ordinata di tutte le conversazioni disponibili.
        """
        self.list_widget.clear()
        
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                
                # Dizionario per raccogliere le chat uniche
                chats = {}
                
                # Itera sui messaggi per estrarre le chat
                for msg in messages:
                    # Ottiene le info della chat (preferisce 'chat' a 'sender')
                    chat = msg.get('chat') or msg.get('sender')
                    
                    if not chat:
                        continue
                    
                    chat_id = chat.get('id')
                    if not chat_id:
                        continue
                    
                    # Determina il titolo della chat da visualizzare
                    chat_title = (chat.get('title') or           # Nome gruppo/canale
                                chat.get('first_name') or        # Nome utente
                                chat.get('username') or          # Username
                                str(chat_id))                    # Fallback: ID
                    
                    # Aggiunge la chat al dizionario se non già presente
                    if chat_id not in chats:
                        chats[chat_id] = {'title': chat_title}
                
                # Crea gli item della lista per ogni chat
                for cid, info in chats.items():
                    item = QListWidgetItem(f"{info['title']}")
                    item.setData(Qt.UserRole, cid)  # Salva l'ID nei dati dell'item
                    self.list_widget.addItem(item)
                    
            except Exception:
                # In caso di errore nella lettura, non mostra chat
                pass

    def show_messages_of_chat(self, item):
        """
        Apre il dialog dei messaggi per la chat selezionata.
        
        Crea e mostra una finestra con tutti i messaggi della chat
        selezionata dall'utente.
        
        Args:
            item (QListWidgetItem): Item della chat selezionata
        """
        # Ottiene l'ID della chat dai dati dell'item
        chat_id = item.data(Qt.UserRole)
        chat_title = item.text()
        
        # Crea e mostra il dialog dei messaggi per questa chat
        dialog = MessagesOfChatDialog(chat_id, chat_title, self)
        dialog.exec()

class MessagesWidget(QWidget):
    """
    Widget principale per la visualizzazione dei messaggi e gestione dell'interfaccia utente.
    
    Questa classe rappresenta la finestra principale dell'applicazione, fornendo
    un'interfaccia per visualizzare i messaggi in tempo reale, accedere ai contatti,
    gestire le chat e controllare la cronologia dei messaggi.
    
    L'interfaccia è divisa in due sezioni:
    - Sinistra: Pulsanti per navigazione (Contatti, Chat, Elimina Cronologia)
    - Destra: Lista dei messaggi ricevuti nella sessione corrente
    
    Attributes:
        contacts_btn (QPushButton): Pulsante per aprire il dialog dei contatti
        chats_btn (QPushButton): Pulsante per aprire il dialog delle chat
        clear_btn (QPushButton): Pulsante per eliminare la cronologia
        list_widget (QListWidget): Lista per visualizzare i messaggi
        placeholder (QLabel): Etichetta mostrata quando non ci sono messaggi
        session_start_time (str): Timestamp di inizio della sessione corrente
        contacts_dialog (ContactsDialog): Dialog dei contatti (se aperto)
    """
    
    def __init__(self):
        """
        Inizializza il widget principale dei messaggi e configura l'interfaccia utente.
        """
        super().__init__()
        self.setWindowTitle('Messaggi Telegram')
        self.setMinimumWidth(420)
        
        # Layout principale orizzontale (pulsanti a sinistra, messaggi a destra)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # === SEZIONE SINISTRA: Pulsanti di navigazione ===
        left_layout = QVBoxLayout()
        
        # Pulsante per aprire il dialog dei contatti
        self.contacts_btn = QPushButton('Contatti')
        self.contacts_btn.setIcon(QIcon.fromTheme('user-group'))
        self.contacts_btn.setMinimumHeight(40)
        self.contacts_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.contacts_btn.clicked.connect(self.open_contacts)
        
        # Pulsante per aprire il dialog delle chat
        self.chats_btn = QPushButton('Chat')
        self.chats_btn.setIcon(QIcon.fromTheme('chat'))
        self.chats_btn.setMinimumHeight(40)
        self.chats_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.chats_btn.clicked.connect(self.open_chats)
        
        # Pulsante per eliminare la cronologia
        self.clear_btn = QPushButton('Elimina Cronologia')
        self.clear_btn.setIcon(QIcon.fromTheme('edit-delete'))
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.clear_btn.clicked.connect(self.clear_history)
        
        # Aggiunge i pulsanti al layout sinistro
        left_layout.addWidget(self.contacts_btn)
        left_layout.addWidget(self.chats_btn)
        left_layout.addWidget(self.clear_btn)
        left_layout.addStretch()  # Spinge i pulsanti verso l'alto
        
        main_layout.addLayout(left_layout)
        
        # === SEZIONE DESTRA: Lista dei messaggi ===
        right_layout = QVBoxLayout()
        
        # Titolo della sezione messaggi
        title = QLabel('Messaggi ricevuti:')
        title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        right_layout.addWidget(title)
        
        # Lista dei messaggi con stile personalizzato
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Segoe UI', 10))
        self.list_widget.setStyleSheet(
            'QListWidget { '
            'background: #222; '      # Sfondo scuro
            'color: #eee; '           # Testo chiaro
            'border-radius: 8px; '    # Bordi arrotondati
            'padding: 8px; '          # Padding interno
            '}'
        )
        right_layout.addWidget(self.list_widget)
        
        # Placeholder mostrato quando non ci sono messaggi
        self.placeholder = QLabel('Nessun messaggio ricevuto in questa sessione.')
        font_placeholder = QFont('Segoe UI', 9)
        font_placeholder.setItalic(True)
        self.placeholder.setFont(font_placeholder)
        self.placeholder.setStyleSheet('color: #888;')  # Testo grigio
        self.placeholder.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.placeholder)
        self.placeholder.hide()  # Nascosto inizialmente
        
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)
        
        # Inizializza le variabili di stato
        self.session_start_time = None    # Timestamp di inizio sessione
        self.contacts_dialog = None       # Reference al dialog dei contatti
        
        # Aggiorna la visibilità del placeholder
        self.update_placeholder()

    def set_session_start_time(self, start_time):
        """
        Imposta il timestamp di inizio della sessione corrente.
        
        Questo metodo viene chiamato quando viene avviato il MessageListener
        per definire da quale momento filtrare i messaggi da visualizzare.
        
        Args:
            start_time (str): Timestamp ISO di inizio della sessione
        """
        self.session_start_time = start_time
        self.load_messages()  # Ricarica i messaggi con il nuovo filtro temporale

    def get_display_name(self, msg):
        """
        Determina il nome da visualizzare per un messaggio.
        
        Analizza le informazioni del messaggio per determinare il nome
        più appropriato da mostrare (gruppo, canale, utente, etc.).
        
        Args:
            msg (dict): Dizionario contenente i dati del messaggio
            
        Returns:
            str: Nome da visualizzare per il mittente del messaggio
        """
        sender = msg.get('sender', {})
        chat = msg.get('chat', {})
        
        # Preferisce il nome del gruppo/canale se presente
        if chat and chat.get('title'):
            return chat.get('title')
        
        # Altrimenti, se è un utente, costruisce il nome completo
        if sender.get('first_name') or sender.get('last_name'):
            full_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            return full_name
        
        # Se non ha nome, usa l'username
        if sender.get('username'):
            return sender.get('username')
        
        # Se non ha username, usa il titolo (per canali/gruppi)
        if sender.get('title'):
            return sender.get('title')
        
        # Fallback: usa l'ID del mittente
        return sender.get('id', msg.get('from_id', 'Sconosciuto'))

    def load_messages(self):
        """
        Carica e visualizza i messaggi della sessione corrente.
        
        Legge tutti i messaggi salvati e filtra quelli ricevuti durante
        la sessione corrente (dopo session_start_time), aggiornando
        la lista nell'interfaccia utente.
        """
        self.list_widget.clear()
        count = 0
        
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                
                # Filtra i messaggi per la sessione corrente
                for msg in messages:
                    # Verifica che il messaggio sia della sessione corrente
                    if (self.session_start_time and 
                        msg.get('received_at') and 
                        msg['received_at'] >= self.session_start_time):
                        
                        # Ottiene il nome da visualizzare
                        display_name = self.get_display_name(msg)
                        
                        # Aggiunge il messaggio alla lista
                        message_text = msg.get('text', '')
                        self.list_widget.addItem(f"Da {display_name}: {message_text}")
                        count += 1
                        
            except Exception:
                # In caso di errore nella lettura, non mostra messaggi
                pass
        
        # Aggiorna la visibilità del placeholder
        self.update_placeholder(count)

    def add_message(self, msg):
        """
        Aggiunge un nuovo messaggio alla lista in tempo reale.
        
        Questo metodo viene chiamato dal MessageListener quando arriva
        un nuovo messaggio, aggiungendolo immediatamente all'interfaccia.
        
        Args:
            msg (dict): Dizionario contenente i dati del nuovo messaggio
        """
        # Verifica che il messaggio sia della sessione corrente
        if (self.session_start_time and 
            msg.get('received_at') and 
            msg['received_at'] >= self.session_start_time):
            
            # Ottiene il nome da visualizzare e aggiunge il messaggio
            display_name = self.get_display_name(msg)
            message_text = msg.get('text', '')
            self.list_widget.addItem(f"Da {display_name}: {message_text}")
        
        # Aggiorna la visibilità del placeholder
        self.update_placeholder()

    def update_placeholder(self, count=None):
        """
        Aggiorna la visibilità del placeholder in base al numero di messaggi.
        
        Mostra il placeholder quando non ci sono messaggi, lo nasconde altrimenti.
        
        Args:
            count (int, optional): Numero di messaggi. Se None, conta gli item nella lista.
        """
        if count is None:
            count = self.list_widget.count()
        
        # Mostra il placeholder solo se non ci sono messaggi
        self.placeholder.setVisible(count == 0)

    def open_contacts(self):
        """
        Apre il dialog per visualizzare i contatti salvati.
        
        Crea e mostra una finestra con tutti i contatti che sono stati
        registrati durante l'uso dell'applicazione.
        """
        if self.contacts_dialog is None:
            self.contacts_dialog = ContactsDialog(self)
        
        # Ricarica i contatti e pulisce i dettagli
        self.contacts_dialog.load_contacts()
        self.contacts_dialog.details.clear()
        
        # Mostra il dialog
        self.contacts_dialog.exec()
        self.contacts_dialog = None

    def open_chats(self):
        """
        Apre il dialog per visualizzare le chat salvate.
        
        Crea e mostra una finestra con tutte le chat da cui sono stati
        ricevuti messaggi, permettendo di visualizzare la cronologia.
        """
        dialog = ChatsDialog(self)
        dialog.exec()

    def clear_history(self):
        """
        Elimina tutta la cronologia dei messaggi e delle immagini.
        
        Chiede conferma all'utente e, se confermato, elimina tutti i dati
        salvati (messaggi e immagini) resettando l'applicazione.
        """
        # Chiede conferma all'utente
        reply = QMessageBox.question(
            self, 
            'Conferma eliminazione',
            'Sei sicuro di voler eliminare tutta la cronologia dei messaggi e delle immagini? '
            'L\'operazione è irreversibile.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Elimina i contenuti dei file di dati
            for file_path in [MESSAGES_FILE, IMAGES_FILE]:
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        # Scrive struttura vuota (lista per messaggi, dict per immagini)
                        empty_data = [] if file_path == MESSAGES_FILE else {}
                        json.dump(empty_data, file)
                except Exception:
                    # Ignora errori nella scrittura
                    pass
            
            # Ricarica la lista dei messaggi (ora vuota)
            self.load_messages()
            
            # Conferma all'utente
            QMessageBox.information(
                self, 
                'Cronologia eliminata', 
                'Tutta la cronologia è stata eliminata con successo.'
            )

class MainApp(QApplication):
    """
    Classe principale dell'applicazione AutomaticTelReader.
    
    Questa classe coordina l'intero flusso dell'applicazione, gestendo:
    - Il processo di autenticazione (login)
    - La transizione tra schermata di login e interfaccia principale
    - L'avvio e gestione del thread di ascolto messaggi
    - La chiusura pulita dell'applicazione
    
    Attributes:
        login_widget (LoginWidget): Widget per il login Telegram
        messages_widget (MessagesWidget): Widget principale per i messaggi
        listener_thread (MessageListener): Thread per l'ascolto dei messaggi
        _should_quit (bool): Flag per il controllo della chiusura dell'app
    """
    
    def __init__(self, argv):
        """
        Inizializza l'applicazione principale.
        
        Configura i widget necessari e determina se mostrare la schermata
        di login o avviare direttamente l'applicazione con credenziali salvate.
        
        Args:
            argv (list): Argomenti della linea di comando
        """
        super().__init__(argv)
        
        # Inizializza i widget principali
        self.login_widget = LoginWidget(self.on_login)
        self.messages_widget = MessagesWidget()
        self.listener_thread = None
        self._should_quit = False
        
        # Controlla se esistono credenziali salvate per auto-login
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Estrae le credenziali dal file di configurazione
                api_id = str(data.get('api_id', ''))
                api_hash = data.get('api_hash', '')
                phone = data.get('phone', '')
                
                # Se tutte le credenziali sono presenti, avvia automaticamente
                if api_id and api_hash and phone:
                    self.on_login(api_id, api_hash, phone)
                else:
                    # Credenziali incomplete: mostra la schermata di login
                    self.login_widget.show()
                    
            except Exception:
                # Errore nella lettura del file: mostra la schermata di login
                self.login_widget.show()
        else:
            # File di configurazione non esiste: primo avvio
            self.login_widget.show()

    def on_login(self, api_id, api_hash, phone):
        """
        Gestisce il processo di login e avvia l'interfaccia principale.
        
        Questo metodo viene chiamato quando l'utente completa il login
        o quando vengano trovate credenziali valide salvate. Nasconde
        la schermata di login e avvia il sistema di monitoraggio messaggi.
        
        Args:
            api_id (str): ID dell'API Telegram
            api_hash (str): Hash dell'API Telegram
            phone (str): Numero di telefono per l'autenticazione
        """
        # Nasconde la schermata di login
        self.login_widget.hide()
        
        # Mostra l'interfaccia principale
        self.messages_widget.show()
        
        # Crea e configura il thread di ascolto messaggi
        self.listener_thread = MessageListener(api_id, api_hash, phone)
        
        # Imposta il timestamp di inizio sessione nel widget messaggi
        self.messages_widget.set_session_start_time(self.listener_thread.start_time)
        
        # Collega il segnale dei nuovi messaggi al widget
        self.listener_thread.new_message.connect(self.messages_widget.add_message)
        
        # Imposta l'handler per la chiusura della finestra principale
        self.messages_widget.closeEvent = self.on_main_window_close
        
        # Avvia il thread di ascolto
        self.listener_thread.start()

    def on_main_window_close(self, event):
        """
        Gestisce la chiusura pulita dell'applicazione.
        
        Questo metodo viene chiamato quando l'utente chiude la finestra
        principale. Si assicura che il thread di ascolto venga terminato
        correttamente prima di chiudere l'applicazione.
        
        Args:
            event (QCloseEvent): Evento di chiusura della finestra
        """
        # Se il thread di ascolto è attivo, lo termina prima di chiudere
        if self.listener_thread and self.listener_thread.isRunning():
            # Richiede l'interruzione del thread
            self.listener_thread.requestInterruption()
            
            # Termina il thread
            self.listener_thread.quit()
            
            # Aspetta massimo 3 secondi per la terminazione
            self.listener_thread.wait(3000)
        
        # Accetta l'evento di chiusura
        event.accept()
        
        # Termina l'applicazione
        self.quit()


# Punto di ingresso dell'applicazione
if __name__ == '__main__':
    """
    Punto di ingresso principale del programma.
    
    Crea un'istanza di MainApp e avvia il loop degli eventi Qt,
    terminando con il codice di uscita appropriato.
    """
    # Crea l'applicazione principale
    app = MainApp(sys.argv)
    
    # Avvia il loop degli eventi e termina con il codice appropriato
    sys.exit(app.exec()) 