import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, 
                               QLineEdit, QMessageBox, QHBoxLayout, QDialog, QTextEdit, QInputDialog, 
                               QDialogButtonBox, QListView, QAbstractItemView, QListWidgetItem, 
                               QProgressBar, QSplashScreen, QFrame, QScrollArea, QGroupBox, 
                               QSpacerItem, QSizePolicy, QCheckBox, QComboBox, QSpinBox)
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QImage, QPalette, QColor, QPainter, QBrush
from telethon import TelegramClient, events
import os
import json
import datetime
from telethon.tl.types import User, Channel, Chat
import base64
import uuid
import yfinance as yf
import requests
from datetime import datetime as dt
IMAGES_FILE = 'images.json'

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
        self.setup_ui()
        self.load_saved_credentials()

    def setup_ui(self):
        self.setWindowTitle('AutomaticTelReader - Login')
        self.setFixedSize(450, 380)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                font-family: 'Segoe UI';
                color: #ffffff;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #555555;
                border-radius: 8px;
                font-size: 13px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                background-color: #404040;
            }
            QLineEdit::placeholder {
                color: #bbbbbb;
            }
            QPushButton {
                padding: 14px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #333333;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #4da6ff;
                font-weight: bold;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid #555555;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titolo principale
        title = QLabel('📱 AutomaticTelReader')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4da6ff; margin-bottom: 10px; padding: 10px;")
        layout.addWidget(title)
        
        # Sottotitolo
        subtitle = QLabel('Inserisci le credenziali Telegram per iniziare')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #cccccc; margin-bottom: 25px; padding: 5px;")
        layout.addWidget(subtitle)
        
        # Gruppo credenziali
        cred_group = QGroupBox("🔐 Credenziali API Telegram")
        cred_layout = QVBoxLayout()
        cred_layout.setSpacing(12)
        
        # Label descrittivo
        info_label = QLabel("💡 Ottieni le credenziali da my.telegram.org/apps")
        info_label.setStyleSheet("font-size: 11px; color: #aaaaaa; font-style: italic; margin-bottom: 8px;")
        cred_layout.addWidget(info_label)
        
        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText('API ID (numero, es: 123456)')
        cred_layout.addWidget(self.api_id_input)
        
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText('API Hash (es: abcd1234efgh5678...)')
        cred_layout.addWidget(self.api_hash_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('Numero di telefono (es: +39123456789)')
        cred_layout.addWidget(self.phone_input)
        
        cred_group.setLayout(cred_layout)
        layout.addWidget(cred_group)
        
        # Checkbox per salvare credenziali
        self.save_creds_checkbox = QCheckBox('Salva credenziali per il prossimo avvio')
        self.save_creds_checkbox.setChecked(True)
        layout.addWidget(self.save_creds_checkbox)
        
        # Pulsante login
        self.login_btn = QPushButton('🚀 Avvia AutomaticTelReader')
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self.try_login)
        layout.addWidget(self.login_btn)
        
        # Link di aiuto
        help_label = QLabel('<a href="#" style="color: #4da6ff; text-decoration: underline; font-weight: bold;">❓ Come ottenere API ID e Hash - Clicca qui</a>')
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("font-size: 12px; padding: 8px; color: #ffffff;")
        help_label.linkActivated.connect(self.show_help)
        layout.addWidget(help_label)
        
        # Aggiunge spazio elastico
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connetti gli eventi per validazione in tempo reale
        self.api_id_input.textChanged.connect(self.validate_inputs)
        self.api_hash_input.textChanged.connect(self.validate_inputs)
        self.phone_input.textChanged.connect(self.validate_inputs)
        
        # Iniziale validazione
        self.validate_inputs()

    def validate_inputs(self):
        """Valida gli input e abilita/disabilita il pulsante login"""
        api_id = self.api_id_input.text().strip()
        api_hash = self.api_hash_input.text().strip()
        phone = self.phone_input.text().strip()
        
        # Verifica che tutti i campi siano compilati
        all_filled = bool(api_id and api_hash and phone)
        
        # Verifica formato telefono (semplice)
        phone_valid = phone.startswith('+') and len(phone) >= 10 if phone else False
        
        # Verifica API ID (dovrebbe essere numerico)
        api_id_valid = api_id.isdigit() if api_id else False
        
        # Abilita il pulsante solo se tutto è valido
        self.login_btn.setEnabled(all_filled and phone_valid and api_id_valid)
        
        # Feedback visuale sui campi
        self.update_field_style(self.api_id_input, api_id_valid if api_id else True)
        self.update_field_style(self.phone_input, phone_valid if phone else True)

    def update_field_style(self, field, is_valid):
        """Aggiorna lo style del campo in base alla validità"""
        base_style = """
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            background-color: #3c3c3c;
            color: #ffffff;
        """
        
        if is_valid:
            field.setStyleSheet(base_style + "border: 2px solid #555555;")
        else:
            field.setStyleSheet(base_style + "border: 2px solid #e74c3c; background-color: #4a2c2c;")

    def show_help(self):
        """Mostra una finestra di aiuto per ottenere le credenziali"""
        help_text = """
        <div style="font-family: 'Segoe UI'; color: #ffffff; line-height: 1.4; background-color: #2b2b2b;">
        <h2 style="color: #4da6ff; margin-bottom: 15px;">🔑 Come ottenere API ID e API Hash</h2>
        
        <p style="margin-bottom: 12px; color: #ffffff;"><strong>Per utilizzare AutomaticTelReader, hai bisogno delle credenziali API di Telegram:</strong></p>
        
        <ol style="margin-left: 20px; margin-bottom: 15px; color: #ffffff;">
        <li style="margin-bottom: 8px;"><strong>Vai su</strong> <a href="https://my.telegram.org" style="color: #4da6ff;">my.telegram.org</a></li>
        <li style="margin-bottom: 8px;"><strong>Accedi</strong> con il tuo numero di telefono Telegram</li>
        <li style="margin-bottom: 8px;"><strong>Vai</strong> alla sezione "API development tools"</li>
        <li style="margin-bottom: 8px;"><strong>Crea una nuova applicazione</strong> inserendo:
            <ul style="margin-left: 15px; margin-top: 5px; color: #cccccc;">
            <li><strong>App title:</strong> AutomaticTelReader</li>
            <li><strong>Short name:</strong> telreader</li>
            <li><strong>Platform:</strong> Desktop</li>
            </ul>
        </li>
        <li style="margin-bottom: 8px;"><strong>Copia</strong> <span style="background: #404040; color: #4da6ff; padding: 2px 6px; border-radius: 3px;">API ID</span> e <span style="background: #404040; color: #4da6ff; padding: 2px 6px; border-radius: 3px;">API Hash</span> nei campi sopra</li>
        </ol>
        
        <div style="background: #4a4a00; border: 1px solid #666600; border-radius: 6px; padding: 12px; margin-top: 15px;">
        <p style="margin: 0; color: #ffeb3b;"><strong>⚠️ Importante:</strong> Queste credenziali sono personali e sicure. Non condividerle mai con nessuno!</p>
        </div>
        </div>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle('Guida - Credenziali API Telegram')
        msg.setText(help_text)
        msg.setTextFormat(Qt.RichText)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                background-color: #2b2b2b;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        msg.exec()

    def load_saved_credentials(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.api_id_input.setText(str(data.get('api_id', '')))
                self.api_hash_input.setText(data.get('api_hash', ''))
                self.phone_input.setText(data.get('phone', ''))
                self.save_creds_checkbox.setChecked(data.get('save_credentials', True))
            except Exception:
                pass

    def try_login(self):
        api_id = self.api_id_input.text().strip()
        api_hash = self.api_hash_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not (api_id and api_hash and phone):
            QMessageBox.warning(self, 'Errore', 'Tutti i campi sono obbligatori!')
            return
        
        if not api_id.isdigit():
            QMessageBox.warning(self, 'Errore', 'API ID deve essere un numero!')
            return
            
        if not phone.startswith('+'):
            QMessageBox.warning(self, 'Errore', 'Il numero di telefono deve iniziare con + (es: +39123456789)')
            return
        
        # Salva le credenziali solo se richiesto
        if self.save_creds_checkbox.isChecked():
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({
                        'api_id': api_id, 
                        'api_hash': api_hash, 
                        'phone': phone,
                        'save_credentials': True
                    }, f)
            except Exception as e:
                QMessageBox.warning(self, 'Avviso', f'Impossibile salvare le credenziali: {str(e)}')
        
        # Disabilita il pulsante durante il login
        self.login_btn.setEnabled(False)
        self.login_btn.setText('🔄 Connessione in corso...')
        
        # Avvia il processo di login
        QTimer.singleShot(100, lambda: self.on_login(api_id, api_hash, phone))

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
            # Salva info gruppo se presente
            chat_info = None
            if hasattr(event, 'chat') and event.chat:
                chat_info = self.extract_sender_info(event.chat)
            image_id = None
            if hasattr(event.message, 'photo') and event.message.photo:
                # Scarica la foto in memoria e codifica in base64
                img_bytes = await self.client.download_media(event.message.photo, file=bytes)
                if img_bytes:
                    image_id = str(uuid.uuid4())
                    self.save_image(image_id, img_bytes, now, sender_info, chat_info)
            msg = {
                'from_id': str(event.sender_id),
                'text': event.raw_text,
                'date': str(event.date),
                'received_at': now,
                'sender': sender_info,
                'chat': chat_info if chat_info else None,
                'image_id': image_id
            }
            self.save_message(msg)
            self.save_contact(sender_info)
            if chat_info:
                self.save_contact(chat_info)
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

    def save_image(self, image_id, img_bytes, date, sender_info, chat_info):
        images = {}
        if os.path.exists(IMAGES_FILE):
            try:
                with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                    images = json.load(f)
            except Exception:
                images = {}
        images[image_id] = {
            'base64': base64.b64encode(img_bytes).decode('utf-8'),
            'date': date,
            'sender': sender_info,
            'chat': chat_info
        }
        with open(IMAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(images, f, ensure_ascii=False, indent=2)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Impostazioni AutomaticTelReader')
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #333333;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4da6ff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QCheckBox, QLabel {
                font-size: 11px;
                color: #ffffff;
            }
            QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Gruppo notifiche
        notifications_group = QGroupBox("🔔 Notifiche")
        notifications_layout = QVBoxLayout()
        
        self.sound_notifications = QCheckBox("Riproduci suono per nuovi messaggi")
        self.desktop_notifications = QCheckBox("Mostra notifiche desktop")
        self.minimize_to_tray = QCheckBox("Minimizza nell'area di notifica")
        
        notifications_layout.addWidget(self.sound_notifications)
        notifications_layout.addWidget(self.desktop_notifications)
        notifications_layout.addWidget(self.minimize_to_tray)
        notifications_group.setLayout(notifications_layout)
        layout.addWidget(notifications_group)
        
        # Gruppo messaggi
        messages_group = QGroupBox("💬 Gestione Messaggi")
        messages_layout = QVBoxLayout()
        
        max_messages_layout = QHBoxLayout()
        max_messages_label = QLabel("Numero massimo di messaggi da visualizzare:")
        max_messages_layout.addWidget(max_messages_label)
        self.max_messages = QSpinBox()
        self.max_messages.setRange(50, 10000)
        self.max_messages.setValue(1000)
        self.max_messages.setSuffix(" messaggi")
        self.max_messages.setMinimumWidth(180)  # Più largo per leggibilità
        max_messages_layout.addWidget(self.max_messages)
        max_messages_layout.addStretch()
        messages_layout.addLayout(max_messages_layout)
        
        self.auto_scroll = QCheckBox("Scorri automaticamente ai nuovi messaggi")
        self.auto_scroll.setChecked(True)
        messages_layout.addWidget(self.auto_scroll)
        
        messages_group.setLayout(messages_layout)
        layout.addWidget(messages_group)
        
        # Gruppo avanzate
        advanced_group = QGroupBox("⚙️ Opzioni Avanzate")
        advanced_layout = QVBoxLayout()
        
        self.auto_save_images = QCheckBox("Salva automaticamente le immagini ricevute")
        self.auto_save_images.setChecked(True)
        
        self.debug_mode = QCheckBox("Modalità debug (maggiori log)")
        
        advanced_layout.addWidget(self.auto_save_images)
        advanced_layout.addWidget(self.debug_mode)
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Ripristina Default")
        reset_btn.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Annulla")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ Salva Impostazioni")
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_settings(self):
        """Carica le impostazioni salvate"""
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.sound_notifications.setChecked(settings.get('sound_notifications', False))
                self.desktop_notifications.setChecked(settings.get('desktop_notifications', True))
                self.minimize_to_tray.setChecked(settings.get('minimize_to_tray', False))
                self.max_messages.setValue(settings.get('max_messages', 1000))
                self.auto_scroll.setChecked(settings.get('auto_scroll', True))
                self.auto_save_images.setChecked(settings.get('auto_save_images', True))
                self.debug_mode.setChecked(settings.get('debug_mode', False))
            except Exception:
                pass

    def save_settings(self):
        """Salva le impostazioni"""
        settings = {
            'sound_notifications': self.sound_notifications.isChecked(),
            'desktop_notifications': self.desktop_notifications.isChecked(),
            'minimize_to_tray': self.minimize_to_tray.isChecked(),
            'max_messages': self.max_messages.value(),
            'auto_scroll': self.auto_scroll.isChecked(),
            'auto_save_images': self.auto_save_images.isChecked(),
            'debug_mode': self.debug_mode.isChecked()
        }
        
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            QMessageBox.information(self, 'Impostazioni salvate', 
                '✅ Le impostazioni sono state salvate correttamente.')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Errore', 
                f'Impossibile salvare le impostazioni: {str(e)}')

    def reset_to_defaults(self):
        """Ripristina le impostazioni predefinite"""
        reply = QMessageBox.question(self, 'Ripristina Default',
            'Sei sicuro di voler ripristinare tutte le impostazioni ai valori predefiniti?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.sound_notifications.setChecked(False)
            self.desktop_notifications.setChecked(True)
            self.minimize_to_tray.setChecked(False)
            self.max_messages.setValue(1000)
            self.auto_scroll.setChecked(True)
            self.auto_save_images.setChecked(True)
            self.debug_mode.setChecked(False)

class ContactsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📞 Contatti Telegram')
        self.setMinimumSize(700, 500)
        self.setup_ui()
        self.load_contacts()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QListWidget {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 5px;
                font-size: 11px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444444;
                border-radius: 4px;
                margin-bottom: 2px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTextEdit {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit::placeholder {
                color: #aaaaaa;
            }
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel('Contatti salvati:')
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Pulsante di ricerca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cerca contatto...")
        self.search_input.textChanged.connect(self.filter_contacts)
        self.search_input.setFixedWidth(200)
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)
        
        # Layout principale con splitter
        main_layout = QHBoxLayout()
        
        # Lista contatti
        contacts_frame = QFrame()
        contacts_frame.setFixedWidth(300)
        contacts_layout = QVBoxLayout(contacts_frame)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.show_contact_details)
        contacts_layout.addWidget(self.list_widget)
        
        # Contatore contatti
        self.count_label = QLabel()
        self.count_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
        contacts_layout.addWidget(self.count_label)
        
        main_layout.addWidget(contacts_frame)
        
        # Pannello dettagli
        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        
        details_layout.addWidget(QLabel('Dettagli contatto:'))
        
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        details_layout.addWidget(self.details)
        
        # Pulsanti azioni
        actions_layout = QHBoxLayout()
        
        export_btn = QPushButton('📤 Esporta Contatti')
        export_btn.clicked.connect(self.export_contacts)
        actions_layout.addWidget(export_btn)
        
        actions_layout.addStretch()
        
        close_btn = QPushButton('✅ Chiudi')
        close_btn.clicked.connect(self.accept)
        actions_layout.addWidget(close_btn)
        
        details_layout.addLayout(actions_layout)
        main_layout.addWidget(details_frame)
        
        layout.addLayout(main_layout)
        self.setLayout(layout)
        
        # Memorizza tutti i contatti per il filtro
        self.all_contacts = {}

    def load_contacts(self):
        self.list_widget.clear()
        self.all_contacts = {}
        
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                self.all_contacts = contacts
                
                for cid, info in contacts.items():
                    self.add_contact_item(cid, info)
                    
            except Exception as e:
                QMessageBox.warning(self, 'Errore', f'Errore nel caricamento contatti: {str(e)}')
        
        self.update_count()

    def add_contact_item(self, cid, info):
        """Aggiunge un elemento contatto alla lista"""
        contact_type = info.get('type', 'unknown')
        
        # Icona basata sul tipo
        if contact_type == 'user':
            icon = "👤"
        elif contact_type == 'channel':
            icon = "📢"
        elif contact_type == 'group':
            icon = "👥"
        else:
            icon = "❓"
        
        # Nome da visualizzare
        display_name = (info.get('title') or 
                       f"{info.get('first_name', '')} {info.get('last_name', '')}".strip() or
                       info.get('username') or 
                       'Sconosciuto')
        
        # Username se presente
        username = info.get('username', '')
        username_text = f" (@{username})" if username else ""
        
        display = f"{icon} {display_name}{username_text}\n📱 ID: {cid}"
        
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, cid)
        self.list_widget.addItem(item)

    def filter_contacts(self):
        """Filtra i contatti in base al testo di ricerca"""
        search_text = self.search_input.text().lower()
        self.list_widget.clear()
        
        if not search_text:
            # Mostra tutti i contatti
            for cid, info in self.all_contacts.items():
                self.add_contact_item(cid, info)
        else:
            # Filtra i contatti
            for cid, info in self.all_contacts.items():
                # Cerca in vari campi
                searchable_text = (
                    info.get('title', '') + ' ' +
                    info.get('first_name', '') + ' ' +
                    info.get('last_name', '') + ' ' +
                    info.get('username', '') + ' ' +
                    str(cid)
                ).lower()
                
                if search_text in searchable_text:
                    self.add_contact_item(cid, info)
        
        self.update_count()

    def update_count(self):
        """Aggiorna il contatore dei contatti"""
        total_count = len(self.all_contacts)
        visible_count = self.list_widget.count()
        
        if visible_count == total_count:
            self.count_label.setText(f"📊 {total_count} contatti totali")
        else:
            self.count_label.setText(f"📊 {visible_count} di {total_count} contatti")

    def show_contact_details(self, item):
        cid = item.data(Qt.UserRole)
        if cid in self.all_contacts:
            info = self.all_contacts[cid]
            
            # Formatta i dettagli in modo più leggibile
            details_text = "=== INFORMAZIONI CONTATTO ===\n\n"
            
            details_text += f"🆔 ID: {cid}\n"
            details_text += f"📝 Tipo: {info.get('type', 'Sconosciuto').title()}\n\n"
            
            if info.get('title'):
                details_text += f"🏷️ Titolo: {info['title']}\n"
            
            if info.get('first_name') or info.get('last_name'):
                name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
                details_text += f"👤 Nome: {name}\n"
            
            if info.get('username'):
                details_text += f"🔗 Username: @{info['username']}\n"
            
            if info.get('phone'):
                details_text += f"📞 Telefono: {info['phone']}\n"
            
            # Informazioni aggiuntive per canali/gruppi
            if info.get('is_verified'):
                details_text += "✅ Account verificato\n"
            
            if info.get('is_scam'):
                details_text += "⚠️ Segnalato come scam\n"
            
            if info.get('is_self'):
                details_text += "👤 Questo sei tu\n"
            
            details_text += "\n=== DATI RAW ===\n"
            details_text += json.dumps(info, indent=2, ensure_ascii=False)
            
            self.details.setText(details_text)

    def export_contacts(self):
        """Esporta i contatti in un file CSV"""
        try:
            import csv
            from datetime import datetime
            
            filename = f"contatti_telegram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'Tipo', 'Nome', 'Username', 'Telefono', 'Titolo']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for cid, info in self.all_contacts.items():
                    name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
                    writer.writerow({
                        'ID': cid,
                        'Tipo': info.get('type', ''),
                        'Nome': name,
                        'Username': info.get('username', ''),
                        'Telefono': info.get('phone', ''),
                        'Titolo': info.get('title', '')
                    })
            
            QMessageBox.information(self, 'Esportazione completata', 
                f'✅ Contatti esportati con successo in:\n{filename}')
                
        except Exception as e:
            QMessageBox.critical(self, 'Errore esportazione', 
                f'❌ Errore durante l\'esportazione:\n{str(e)}')

class ImageDialog(QDialog):
    def __init__(self, image_base64, sender_info=None, date=None, parent=None):
        super().__init__(parent)
        self.image_base64 = image_base64
        self.sender_info = sender_info or {}
        self.date = date
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle('🖼️ Visualizzatore Immagine')
        self.setMinimumSize(500, 400)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QFrame {
                border: 1px solid #555;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header con informazioni
        if self.sender_info or self.date:
            info_frame = QFrame()
            info_frame.setStyleSheet("background-color: #3c3c3c; padding: 10px;")
            info_layout = QHBoxLayout(info_frame)
            
            if self.sender_info:
                sender_name = (self.sender_info.get('title') or 
                             f"{self.sender_info.get('first_name', '')} {self.sender_info.get('last_name', '')}".strip() or
                             self.sender_info.get('username') or 
                             'Sconosciuto')
                sender_label = QLabel(f"👤 Da: {sender_name}")
                info_layout.addWidget(sender_label)
            
            if self.date:
                try:
                    date_obj = datetime.datetime.fromisoformat(self.date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%d/%m/%Y %H:%M:%S')
                    date_label = QLabel(f"📅 {formatted_date}")
                    info_layout.addWidget(date_label)
                except:
                    pass
            
            info_layout.addStretch()
            layout.addWidget(info_frame)
        
        # Contenitore immagine con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #1e1e1e; }")
        
        # Carica e mostra l'immagine
        try:
            img_bytes = base64.b64decode(self.image_base64)
            image = QImage.fromData(img_bytes)
            
            if not image.isNull():
                self.pixmap = QPixmap.fromImage(image)
                
                self.image_label = QLabel()
                self.image_label.setAlignment(Qt.AlignCenter)
                self.image_label.setStyleSheet("background-color: #1e1e1e;")
                
                # Inizializza il fattore di scala e il label zoom
                self.scale_factor = 1.0
                self.zoom_label = QLabel('100%')  # Inizializza qui per evitare errori
                
                # Scala l'immagine per adattarla inizialmente
                scroll_area.setWidget(self.image_label)
                QTimer.singleShot(0, self.reset_zoom)
            else:
                error_label = QLabel("❌ Impossibile caricare l'immagine")
                error_label.setAlignment(Qt.AlignCenter)
                scroll_area.setWidget(error_label)
                
        except Exception as e:
            error_label = QLabel(f"❌ Errore nel caricamento: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            scroll_area.setWidget(error_label)
        
        layout.addWidget(scroll_area)
        
        # Controlli zoom
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet("background-color: #3c3c3c; padding: 5px;")
        zoom_layout = QHBoxLayout(zoom_frame)
        
        zoom_out_btn = QPushButton('🔍-')
        zoom_out_btn.setFixedSize(40, 30)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        # Usa il zoom_label già inizializzato o crea uno nuovo
        if not hasattr(self, 'zoom_label') or self.zoom_label is None:
            self.zoom_label = QLabel('100%')
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFixedWidth(60)
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton('🔍+')
        zoom_in_btn.setFixedSize(40, 30)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        zoom_layout.addStretch()
        
        # Pulsante reset zoom
        reset_zoom_btn = QPushButton('🔄 Adatta')
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(reset_zoom_btn)
        
        # Pulsante salva
        save_btn = QPushButton('💾 Salva Come...')
        save_btn.clicked.connect(self.save_image)
        zoom_layout.addWidget(save_btn)
        
        layout.addWidget(zoom_frame)
        
        # Pulsanti finali
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton('✅ Chiudi')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def update_image_display(self):
        """Aggiorna la visualizzazione dell'immagine con il fattore di scala corrente"""
        if hasattr(self, 'pixmap') and hasattr(self, 'image_label'):
            scaled_pixmap = self.pixmap.scaled(
                self.pixmap.size() * self.scale_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
            # Aggiorna il label dello zoom solo se esiste
            if hasattr(self, 'zoom_label') and self.zoom_label:
                self.zoom_label.setText(f'{int(self.scale_factor * 100)}%')

    def zoom_in(self):
        """Aumenta lo zoom"""
        if self.scale_factor < 5.0:  # Massimo 500%
            self.scale_factor *= 1.25
            self.update_image_display()

    def zoom_out(self):
        """Diminuisce lo zoom"""
        if self.scale_factor > 0.1:  # Minimo 10%
            self.scale_factor /= 1.25
            self.update_image_display()

    def reset_zoom(self):
        """Reimposta lo zoom per adattare l'immagine alla finestra"""
        if hasattr(self, 'pixmap'):
            # Calcola il fattore per adattare l'immagine alla finestra
            window_size = self.size()
            pixmap_size = self.pixmap.size()
            
            scale_w = (window_size.width() - 100) / pixmap_size.width()
            scale_h = (window_size.height() - 200) / pixmap_size.height()
            
            self.scale_factor = min(scale_w, scale_h, 1.0)  # Non ingrandire oltre 100%
            self.update_image_display()

    def save_image(self):
        """Salva l'immagine su disco"""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                'Salva Immagine',
                f'immagine_telegram_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                'Immagini PNG (*.png);;Immagini JPEG (*.jpg);;Tutti i file (*)'
            )
            
            if filename:
                img_bytes = base64.b64decode(self.image_base64)
                with open(filename, 'wb') as f:
                    f.write(img_bytes)
                
                QMessageBox.information(self, 'Salvataggio completato',
                    f'✅ Immagine salvata con successo:\n{filename}')
                    
        except Exception as e:
            QMessageBox.critical(self, 'Errore salvataggio',
                f'❌ Errore durante il salvataggio:\n{str(e)}')

    def wheelEvent(self, event):
        """Gestisce lo zoom con la rotella del mouse"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

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
                # Visualizzazione stile WhatsApp
                if image_id and not text.strip():
                    text = "[Immagine]"
                elif image_id and text.strip():
                    text = f"[Immagine] {text}"
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
            image_data = self.load_image_data(image_id)
            if image_data:
                image_b64 = image_data.get('base64')
                sender_info = image_data.get('sender')
                date = image_data.get('date')
                if image_b64:
                    self.image_dialog = ImageDialog(image_b64, sender_info, date, self)
                    self.image_dialog.exec()
                    self.image_dialog = None

    def load_image_data(self, image_id):
        if os.path.exists(IMAGES_FILE):
            with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                images = json.load(f)
            return images.get(image_id)
        return None

class TradingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📈 Trading Forex - Dati Reali')
        self.setMinimumSize(900, 700)
        self.forex_data = {}
        self.setup_ui()
        self.load_real_forex_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QListWidget {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 5px;
                font-size: 12px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #444444;
                border-radius: 4px;
                margin-bottom: 2px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLabel {
                font-size: 12px;
                color: #ffffff;
            }
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #333333;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4da6ff;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Pannello sinistro con lista forex
        left_frame = QFrame()
        left_frame.setFixedWidth(320)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        # Titolo lista forex
        forex_title = QLabel('💱 Coppie Forex in Tempo Reale')
        forex_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4da6ff;")
        left_layout.addWidget(forex_title)
        
        # Status di caricamento
        self.loading_label = QLabel('🔄 Caricamento dati in corso...')
        self.loading_label.setStyleSheet("font-size: 11px; color: #cccccc; font-style: italic;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.loading_label)
        
        # Lista forex
        self.forex_list = QListWidget()
        self.forex_list.itemClicked.connect(self.on_forex_selected)
        left_layout.addWidget(self.forex_list)
        
        # Informazioni aggiuntive
        info_label = QLabel('💡 Dati forniti da Yahoo Finance\n📊 Clicca su una coppia per dettagli')
        info_label.setStyleSheet("font-size: 10px; color: #aaaaaa; font-style: italic;")
        info_label.setWordWrap(True)
        left_layout.addWidget(info_label)
        
        layout.addWidget(left_frame)
        
        # Pannello destro con dettagli
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Titolo dettagli
        self.details_title = QLabel('📊 Seleziona una coppia forex')
        self.details_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        right_layout.addWidget(self.details_title)
        
        # Gruppo quotazioni in tempo reale
        quote_group = QGroupBox("💹 Quotazione Attuale")
        quote_layout = QVBoxLayout()
        
        self.current_price_label = QLabel("Prezzo: -")
        self.current_price_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4da6ff;")
        
        self.change_label = QLabel("Variazione: -")
        self.change_percent_label = QLabel("Variazione %: -")
        self.bid_ask_label = QLabel("Bid/Ask: -")
        self.last_update_label = QLabel("Ultimo aggiornamento: -")
        self.last_update_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
        
        quote_layout.addWidget(self.current_price_label)
        quote_layout.addWidget(self.change_label)
        quote_layout.addWidget(self.change_percent_label)
        quote_layout.addWidget(self.bid_ask_label)
        quote_layout.addWidget(self.last_update_label)
        quote_group.setLayout(quote_layout)
        right_layout.addWidget(quote_group)
        
        # Gruppo informazioni di base
        basic_info_group = QGroupBox("ℹ️ Informazioni di Base")
        basic_info_layout = QVBoxLayout()
        
        self.pair_name_label = QLabel("Nome: -")
        self.pair_description_label = QLabel("Descrizione: -")
        self.market_cap_label = QLabel("Volume: -")
        
        basic_info_layout.addWidget(self.pair_name_label)
        basic_info_layout.addWidget(self.pair_description_label)
        basic_info_layout.addWidget(self.market_cap_label)
        basic_info_group.setLayout(basic_info_layout)
        right_layout.addWidget(basic_info_group)
        
        # Gruppo dati storici
        historical_group = QGroupBox("� Dati Storici (52 settimane)")
        historical_layout = QVBoxLayout()
        
        self.high_52w_label = QLabel("Massimo 52w: -")
        self.low_52w_label = QLabel("Minimo 52w: -")
        self.range_52w_label = QLabel("Range 52w: -")
        
        historical_layout.addWidget(self.high_52w_label)
        historical_layout.addWidget(self.low_52w_label)
        historical_layout.addWidget(self.range_52w_label)
        historical_group.setLayout(historical_layout)
        right_layout.addWidget(historical_group)
        
        # Spazio elastico
        right_layout.addStretch()
        
        # Pulsanti azioni
        actions_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton('🔄 Aggiorna Dati')
        self.refresh_btn.clicked.connect(self.refresh_data)
        actions_layout.addWidget(self.refresh_btn)
        
        actions_layout.addStretch()
        
        close_btn = QPushButton('✅ Chiudi')
        close_btn.clicked.connect(self.accept)
        actions_layout.addWidget(close_btn)
        
        right_layout.addLayout(actions_layout)
        layout.addWidget(right_frame)
        
        self.setLayout(layout)

    def load_real_forex_data(self):
        """Carica dati forex reali da Yahoo Finance"""
        # Lista delle principali coppie forex con i loro simboli Yahoo Finance
        forex_symbols = {
            "EURUSD=X": {"name": "Euro / Dollaro Americano", "pair": "EUR/USD"},
            "GBPUSD=X": {"name": "Sterlina / Dollaro Americano", "pair": "GBP/USD"},
            "USDJPY=X": {"name": "Dollaro Americano / Yen Giapponese", "pair": "USD/JPY"},
            "AUDUSD=X": {"name": "Dollaro Australiano / Dollaro Americano", "pair": "AUD/USD"},
            "USDCAD=X": {"name": "Dollaro Americano / Dollaro Canadese", "pair": "USD/CAD"},
            "USDCHF=X": {"name": "Dollaro Americano / Franco Svizzero", "pair": "USD/CHF"},
            "NZDUSD=X": {"name": "Dollaro Neozelandese / Dollaro Americano", "pair": "NZD/USD"},
            "EURGBP=X": {"name": "Euro / Sterlina", "pair": "EUR/GBP"},
            "EURJPY=X": {"name": "Euro / Yen Giapponese", "pair": "EUR/JPY"},
            "GBPJPY=X": {"name": "Sterlina / Yen Giapponese", "pair": "GBP/JPY"}
        }
        
        self.loading_label.setText('🔄 Caricamento dati da Yahoo Finance...')
        self.forex_list.clear()
        
        # Carica i dati per ogni coppia
        loaded_count = 0
        for symbol, info in forex_symbols.items():
            try:
                # Scarica i dati usando yfinance
                ticker = yf.Ticker(symbol)
                data = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[-1]
                    high_price = hist['High'].iloc[-1]
                    low_price = hist['Low'].iloc[-1]
                    volume = hist['Volume'].iloc[-1] if 'Volume' in hist else 0
                    
                    # Calcola la variazione
                    change = current_price - open_price
                    change_percent = (change / open_price) * 100 if open_price != 0 else 0
                    
                    # Ottieni dati storici per 52 settimane
                    hist_52w = ticker.history(period="1y")
                    high_52w = hist_52w['High'].max() if not hist_52w.empty else current_price
                    low_52w = hist_52w['Low'].min() if not hist_52w.empty else current_price
                    
                    forex_info = {
                        'symbol': symbol,
                        'name': info['name'],
                        'pair': info['pair'],
                        'current_price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'high': high_price,
                        'low': low_price,
                        'volume': volume,
                        'high_52w': high_52w,
                        'low_52w': low_52w,
                        'bid': data.get('bid', current_price),
                        'ask': data.get('ask', current_price),
                        'last_update': dt.now().strftime('%H:%M:%S')
                    }
                    
                    self.forex_data[symbol] = forex_info
                    
                    # Crea l'item per la lista
                    change_color = "🟢" if change >= 0 else "🔴"
                    change_text = f"+{change:.4f}" if change >= 0 else f"{change:.4f}"
                    
                    item_text = f"💱 {info['pair']}\n   {current_price:.4f} {change_color} {change_text} ({change_percent:+.2f}%)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, symbol)
                    
                    # Colore in base al trend
                    if change >= 0:
                        item.setBackground(QColor('#28a745').darker(150))
                    else:
                        item.setBackground(QColor('#dc3545').darker(150))
                    
                    self.forex_list.addItem(item)
                    loaded_count += 1
                    
                    # Aggiorna il label di caricamento
                    self.loading_label.setText(f'🔄 Caricati {loaded_count}/{len(forex_symbols)} coppie...')
                    
            except Exception as e:
                print(f"Errore nel caricamento di {symbol}: {str(e)}")
                continue
        
        # Aggiorna il label finale
        if loaded_count > 0:
            self.loading_label.setText(f'✅ {loaded_count} coppie caricate - Aggiornato: {dt.now().strftime("%H:%M:%S")}')
        else:
            self.loading_label.setText('❌ Errore nel caricamento - Controlla la connessione internet')

    def on_forex_selected(self, item):
        """Gestisce la selezione di una coppia forex"""
        symbol = item.data(Qt.UserRole)
        if symbol and symbol in self.forex_data:
            data = self.forex_data[symbol]
            
            # Aggiorna il titolo
            self.details_title.setText(f"� {data['pair']} - {data['name']}")
            
            # Aggiorna quotazione attuale
            self.current_price_label.setText(f"Prezzo: {data['current_price']:.4f}")
            
            # Colore per la variazione
            if data['change'] >= 0:
                change_color = "#28a745"  # Verde
                change_symbol = "🟢 +"
            else:
                change_color = "#dc3545"  # Rosso
                change_symbol = "🔴 "
            
            self.change_label.setText(f"Variazione: {change_symbol}{data['change']:.4f}")
            self.change_label.setStyleSheet(f"color: {change_color}; font-weight: bold;")
            
            self.change_percent_label.setText(f"Variazione %: {change_symbol}{data['change_percent']:.2f}%")
            self.change_percent_label.setStyleSheet(f"color: {change_color}; font-weight: bold;")
            
            self.bid_ask_label.setText(f"Bid/Ask: {data['bid']:.4f} / {data['ask']:.4f}")
            self.last_update_label.setText(f"Ultimo aggiornamento: {data['last_update']}")
            
            # Aggiorna informazioni di base
            self.pair_name_label.setText(f"Nome: {data['name']}")
            self.pair_description_label.setText(f"Simbolo: {data['symbol']}")
            
            if data['volume'] > 0:
                self.market_cap_label.setText(f"Volume: {data['volume']:,.0f}")
            else:
                self.market_cap_label.setText("Volume: N/A (forex)")
            
            # Aggiorna dati storici
            self.high_52w_label.setText(f"Massimo 52w: {data['high_52w']:.4f}")
            self.low_52w_label.setText(f"Minimo 52w: {data['low_52w']:.4f}")
            
            range_52w = data['high_52w'] - data['low_52w']
            self.range_52w_label.setText(f"Range 52w: {range_52w:.4f}")

    def refresh_data(self):
        """Aggiorna i dati forex"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText('🔄 Aggiornamento...')
        
        # Ricarica i dati
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        """Esegue l'aggiornamento effettivo"""
        try:
            self.load_real_forex_data()
            QMessageBox.information(self, 'Aggiornamento Completato', 
                f'✅ Dati forex aggiornati con successo!\n\nUltimo aggiornamento: {dt.now().strftime("%H:%M:%S")}')
        except Exception as e:
            QMessageBox.warning(self, 'Errore Aggiornamento', 
                f'❌ Errore durante l\'aggiornamento:\n{str(e)}\n\nControlla la connessione internet.')
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText('🔄 Aggiorna Dati')

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

class MessageItemWidget(QWidget):
    """Widget personalizzato per visualizzare un messaggio con eventuale anteprima immagine"""
    
    def __init__(self, msg_data, parent=None):
        super().__init__(parent)
        self.msg_data = msg_data
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Layout principale per testo
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # Header con ora e mittente
        display_name = self.get_display_name()
        try:
            date_obj = datetime.datetime.fromisoformat(self.msg_data.get('date', '').replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%H:%M:%S')
        except:
            formatted_date = "N/A"
        
        icon = "👤" if self.msg_data.get('sender', {}).get('type') == 'user' else "📢"
        
        header_label = QLabel(f"{icon} {formatted_date} | {display_name}")
        header_label.setStyleSheet("font-size: 11px; color: #cccccc; font-weight: bold;")
        text_layout.addWidget(header_label)
        
        # Testo del messaggio
        text = self.msg_data.get('text', '')
        image_id = self.msg_data.get('image_id')

        # Visualizzazione stile WhatsApp
        if image_id and not text.strip():
            text = "[Immagine]"
        elif image_id and text.strip():
            text = f"[Immagine] {text}"

        if len(text) > 100:
            text = text[:100] + "..."

        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 12px; color: #ffffff;")
        text_label.setWordWrap(True)
        text_layout.addWidget(text_label)
        
        layout.addLayout(text_layout)
        
        # Anteprima immagine se presente
        if image_id:
            image_data = self.load_image_data(image_id)
            if image_data and image_data.get('base64'):
                try:
                    # Crea thumbnail dell'immagine
                    img_bytes = base64.b64decode(image_data['base64'])
                    image = QImage.fromData(img_bytes)
                    if not image.isNull():
                        # Ridimensiona l'immagine per la thumbnail mantenendo l'aspect ratio
                        thumbnail = image.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        pixmap = QPixmap.fromImage(thumbnail)
                        
                        # Crea label per l'immagine con contenimento corretto
                        image_label = QLabel()
                        image_label.setPixmap(pixmap)
                        image_label.setStyleSheet("""
                            border: 2px solid #0078d4;
                            border-radius: 4px;
                            background-color: #404040;
                        """)
                        image_label.setFixedSize(54, 54)
                        image_label.setAlignment(Qt.AlignCenter)
                        image_label.setScaledContents(False)  # Evita lo sfondamento
                        image_label.setToolTip("🖼️ Clicca per ingrandire")
                        
                        layout.addWidget(image_label)
                except Exception as e:
                    # Se c'è un errore nel caricamento, mostra icona generica
                    icon_label = QLabel("🖼️")
                    icon_label.setStyleSheet("""
                        font-size: 24px;
                        border: 2px solid #666666;
                        border-radius: 4px;
                        background-color: #404040;
                        color: #cccccc;
                    """)
                    icon_label.setFixedSize(54, 54)
                    icon_label.setAlignment(Qt.AlignCenter)
                    icon_label.setToolTip("🖼️ Immagine (clicca per visualizzare)")
                    layout.addWidget(icon_label)
            else:
                # Se non si riesce a caricare l'immagine, mostra icona generica
                icon_label = QLabel("🖼️")
                icon_label.setStyleSheet("""
                    font-size: 24px;
                    border: 2px solid #666666;
                    border-radius: 4px;
                    background-color: #404040;
                    color: #cccccc;
                """)
                icon_label.setFixedSize(54, 54)
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setToolTip("🖼️ Immagine (clicca per visualizzare)")
                layout.addWidget(icon_label)
        
        self.setLayout(layout)
        
        # Imposta dimensione fissa per evitare problemi di layout
        self.setFixedHeight(70)
        
        # Stile del widget
        self.setStyleSheet("""
            MessageItemWidget {
                background-color: transparent;
                border-radius: 4px;
            }
        """)
    
    def get_display_name(self):
        """Ottiene il nome da visualizzare per il mittente"""
        sender = self.msg_data.get('sender', {})
        chat = self.msg_data.get('chat', {})
        
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
        return sender.get('id', self.msg_data.get('from_id', ''))
    
    def load_image_data(self, image_id):
        """Carica i dati di un'immagine dal file JSON"""
        if os.path.exists(IMAGES_FILE):
            try:
                with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                    images = json.load(f)
                return images.get(image_id)
            except Exception:
                pass
        return None

class MessagesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.session_start_time = None
        self.contacts_dialog = None
        self.message_count = 0

    def setup_ui(self):
        self.setWindowTitle('AutomaticTelReader - Monitor Messaggi')
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                font-family: 'Segoe UI';
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 12px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QListWidget {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
                color: #ffffff;
                alternate-background-color: #3a3a3a;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444444;
                border-radius: 4px;
                margin-bottom: 2px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #333333;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4da6ff;
            }
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 12px;
            }
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Pannello laterale sinistro
        left_panel = QFrame()
        left_panel.setFixedWidth(200)
        left_panel.setStyleSheet("QFrame { background-color: #333333; border-radius: 12px; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        # Logo/Titolo nel pannello
        title_label = QLabel("📱 AutomaticTelReader")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4da6ff; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
        
        # Contatore messaggi
        self.status_label = QLabel("🔄 In attesa di messaggi...")
        self.status_label.setStyleSheet("font-size: 10px; color: #cccccc; margin-bottom: 15px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)
        
        # Pulsanti di navigazione
        self.contacts_btn = QPushButton('👥 Contatti')
        self.contacts_btn.clicked.connect(self.open_contacts)
        left_layout.addWidget(self.contacts_btn)
        
        self.chats_btn = QPushButton('💬 Chat')
        self.chats_btn.clicked.connect(self.open_chats)
        left_layout.addWidget(self.chats_btn)
        
        
        # Pulsanti di utilità
        self.settings_btn = QPushButton('⚙️ Impostazioni')
        self.settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(self.settings_btn)
        
        self.trading_btn = QPushButton('📈 Trading')
        self.trading_btn.clicked.connect(self.open_trading)
        left_layout.addWidget(self.trading_btn)
        
        self.clear_btn = QPushButton('🗑️ Elimina Cronologia')
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_history)
        left_layout.addWidget(self.clear_btn)
        
        left_layout.addStretch()
        
        # Info versione
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("font-size: 9px; color: #888888;")
        version_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(version_label)
        
        main_layout.addWidget(left_panel)
        
        # Pannello principale dei messaggi
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #333333; border-radius: 12px; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Header dei messaggi
        header_layout = QHBoxLayout()
        messages_title = QLabel('📨 Messaggi Ricevuti in Tempo Reale')
        messages_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(messages_title)
        
        header_layout.addStretch()
        
        # Pulsante di refresh
        self.refresh_btn = QPushButton('🔄 Aggiorna')
        self.refresh_btn.setFixedSize(100, 30)
        self.refresh_btn.clicked.connect(self.load_messages)
        header_layout.addWidget(self.refresh_btn)
        
        right_layout.addLayout(header_layout)
        
        # Lista messaggi con scroll personalizzato
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet(self.list_widget.styleSheet() + """
            QListWidget::item {
                min-height: 60px;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #404040;
                border: 1px solid #0078d4;
                border-radius: 4px;
            }
        """)
        # Connetti il segnale di click per visualizzare le immagini
        self.list_widget.itemClicked.connect(self.on_message_clicked)
        right_layout.addWidget(self.list_widget)
        
        # Placeholder per quando non ci sono messaggi
        self.placeholder = QLabel('🔍 Nessun messaggio ricevuto in questa sessione.\n\nI nuovi messaggi appariranno qui automaticamente.')
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            font-size: 14px; 
            color: #aaaaaa; 
            background-color: #3a3a3a; 
            border: 2px dashed #555555; 
            border-radius: 8px; 
            padding: 40px;
        """)
        self.placeholder.setWordWrap(True)
        right_layout.addWidget(self.placeholder)
        self.placeholder.hide()
        
        main_layout.addWidget(right_panel)
        self.setLayout(main_layout)
        
        # Timer per aggiornamenti periodici dell'interfaccia
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_status)
        self.ui_timer.start(5000)  # Aggiorna ogni 5 secondi

    def update_status(self):
        """Aggiorna le informazioni di stato nell'interfaccia"""
        if self.session_start_time:
            # Calcola tempo di attività
            now = datetime.datetime.utcnow()
            if isinstance(self.session_start_time, str):
                start_time = datetime.datetime.fromisoformat(self.session_start_time)
            else:
                start_time = self.session_start_time
            
            uptime = now - start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            status_text = f"✅ Connesso\n📊 {self.message_count} messaggi\n⏱️ {hours:02d}:{minutes:02d}"
            self.status_label.setText(status_text)
        else:
            self.status_label.setText("🔄 Connessione in corso...")

    def on_message_clicked(self, item):
        """Gestisce il click su un messaggio per visualizzare eventuali immagini"""
        try:
            msg_data = item.data(Qt.UserRole)
            if msg_data and msg_data.get('image_id'):
                image_id = msg_data['image_id']
                image_data = self.load_image_data(image_id)
                
                if image_data:
                    image_b64 = image_data.get('base64')
                    sender_info = msg_data.get('sender', {})
                    date = msg_data.get('date')
                    
                    if image_b64:
                        # Crea e mostra il dialog dell'immagine
                        image_dialog = ImageDialog(image_b64, sender_info, date, self)
                        image_dialog.exec()
                else:
                    QMessageBox.warning(self, 'Immagine non trovata', 
                        'L\'immagine associata a questo messaggio non è più disponibile.')
        except Exception as e:
            QMessageBox.critical(self, 'Errore', 
                f'Errore durante il caricamento dell\'immagine: {str(e)}')

    def load_image_data(self, image_id):
        """Carica i dati di un'immagine dal file JSON"""
        if os.path.exists(IMAGES_FILE):
            try:
                with open(IMAGES_FILE, 'r', encoding='utf-8') as f:
                    images = json.load(f)
                return images.get(image_id)
            except Exception:
                pass
        return None

    def open_settings(self):
        """Apre una finestra delle impostazioni"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def open_trading(self):
        """Apre la finestra del trading forex"""
        trading_dialog = TradingDialog(self)
        trading_dialog.exec()

    def set_session_start_time(self, start_time):
        self.session_start_time = start_time
        self.load_messages()
        self.update_status()

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
                    # Crea il widget personalizzato per il messaggio
                    message_widget = MessageItemWidget(msg)
                    
                    # Crea un item per la lista
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(400, 70))  # Dimensione fissa
                    
                    # Salva i dati del messaggio nell'item per il click
                    item.setData(Qt.UserRole, msg)
                    
                    # Aggiungi l'item alla lista
                    self.list_widget.addItem(item)
                    self.list_widget.setItemWidget(item, message_widget)
                    
                    count += 1
        
        self.message_count = count
        self.update_placeholder(count)
        self.update_status()

    def add_message(self, msg):
        if self.session_start_time and msg.get('received_at') and msg['received_at'] >= self.session_start_time:
            # Crea il widget personalizzato per il messaggio
            message_widget = MessageItemWidget(msg)
            
            # Crea un item per la lista
            item = QListWidgetItem()
            item.setSizeHint(QSize(400, 70))  # Dimensione fissa
            
            # Salva i dati del messaggio nell'item per il click
            item.setData(Qt.UserRole, msg)
            
            # Aggiungi l'item alla lista
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, message_widget)
            
            self.message_count += 1
            
            # Scorri automaticamente verso il basso
            self.list_widget.scrollToBottom()
        
        self.update_placeholder()
        self.update_status()

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
            'Sei sicuro di voler eliminare tutta la cronologia dei messaggi e delle immagini?\n\nL\'operazione è irreversibile.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                for f in [MESSAGES_FILE, IMAGES_FILE]:
                    with open(f, 'w', encoding='utf-8') as file:
                        json.dump([] if f == MESSAGES_FILE else {}, file)
                self.message_count = 0
                self.load_messages()
                QMessageBox.information(self, 'Operazione completata', 
                    '✅ Tutta la cronologia è stata eliminata con successo.')
            except Exception as e:
                QMessageBox.critical(self, 'Errore', f'Errore durante l\'eliminazione: {str(e)}')

class MainApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyle('Fusion')  # Usa stile moderno
        self.login_widget = LoginWidget(self.on_login)
        self.messages_widget = MessagesWidget()
        self.listener_thread = None
        self._should_quit = False
        
        # Applica tema generale
        self.setStyleSheet("""
            QApplication {
                font-family: 'Segoe UI';
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                background-color: #2b2b2b;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        # Prova auto-login se le credenziali sono salvate
        self.try_auto_login()

    def try_auto_login(self):
        """Tenta il login automatico se le credenziali sono disponibili"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                api_id = str(data.get('api_id', ''))
                api_hash = data.get('api_hash', '')
                phone = data.get('phone', '')
                save_creds = data.get('save_credentials', False)
                
                if api_id and api_hash and phone and save_creds:
                    # Mostra splash screen durante il login automatico
                    self.show_splash_screen()
                    QTimer.singleShot(1000, lambda: self.on_login(api_id, api_hash, phone, auto_login=True))
                else:
                    self.login_widget.show()
            except Exception as e:
                print(f"Errore nel caricamento config: {e}")
                self.login_widget.show()
        else:
            self.login_widget.show()

    def show_splash_screen(self):
        """Mostra uno splash screen durante il caricamento"""
        splash = QSplashScreen()
        splash.setFixedSize(400, 200)
        
        # Crea un'immagine di sfondo personalizzata
        pixmap = QPixmap(400, 200)
        pixmap.fill(QColor('#0078d4'))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Disegna il testo
        painter.setPen(QColor('white'))
        painter.setFont(QFont('Segoe UI', 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, '📱 AutomaticTelReader\n\n🔄 Connessione in corso...')
        painter.end()
        
        splash.setPixmap(pixmap)
        splash.show()
        
        # Nascondi lo splash dopo 3 secondi
        QTimer.singleShot(3000, splash.close)

    def on_login(self, api_id, api_hash, phone, auto_login=False):
        """Gestisce il processo di login"""
        try:
            self.login_widget.hide()
            
            # Mostra finestra principale
            self.messages_widget.show()
            
            # Crea e avvia il thread di ascolto
            self.listener_thread = MessageListener(api_id, api_hash, phone)
            self.messages_widget.set_session_start_time(self.listener_thread.start_time)
            self.listener_thread.new_message.connect(self.messages_widget.add_message)
            
            # Gestisci la chiusura della finestra
            self.messages_widget.closeEvent = self.on_main_window_close
            
            # Connetti segnali per gestione errori
            self.listener_thread.finished.connect(self.on_listener_finished)
            
            # Avvia il thread
            self.listener_thread.start()
            
        except Exception as e:
            error_msg = f"Errore durante il login: {str(e)}"
            
            if auto_login:
                # In caso di auto-login fallito, mostra il form di login
                QMessageBox.warning(None, 'Login automatico fallito', 
                    f'{error_msg}\n\nInserire nuovamente le credenziali.')
                self.login_widget.show()
            else:
                QMessageBox.critical(None, 'Errore di connessione', error_msg)
                # Riabilita il pulsante di login
                self.login_widget.login_btn.setEnabled(True)
                self.login_widget.login_btn.setText('🚀 Avvia AutomaticTelReader')
                self.login_widget.show()

    def on_listener_finished(self):
        """Chiamato quando il thread di ascolto termina"""
        if not self._should_quit:
            # Se il thread termina inaspettatamente, mostra un messaggio
            reply = QMessageBox.question(
                self.messages_widget,
                'Connessione persa',
                'La connessione a Telegram è stata persa.\n\nVuoi riavviare l\'applicazione?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Riavvia l'applicazione
                self.messages_widget.hide()
                self.login_widget.show()
            else:
                self.quit()

    def on_main_window_close(self, event):
        """Gestisce la chiusura della finestra principale"""
        reply = QMessageBox.question(
            self.messages_widget,
            'Conferma chiusura',
            'Sei sicuro di voler chiudere AutomaticTelReader?\n\nL\'ascolto dei messaggi verrà interrotto.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._should_quit = True
            
            if self.listener_thread and self.listener_thread.isRunning():
                # Mostra dialogo di chiusura
                progress = QMessageBox(self.messages_widget)
                progress.setWindowTitle('Chiusura in corso...')
                progress.setText('🔄 Disconnessione da Telegram...')
                progress.setStandardButtons(QMessageBox.NoButton)
                progress.setWindowFlag(Qt.WindowCloseButtonHint, False)
                progress.show()
                
                # Ferma il thread
                self.listener_thread.requestInterruption()
                self.listener_thread.quit()
                
                # Aspetta massimo 5 secondi per la chiusura
                if not self.listener_thread.wait(5000):
                    self.listener_thread.terminate()
                    self.listener_thread.wait(2000)
                
                progress.close()
            
            event.accept()
            self.quit()
        else:
            event.ignore()

if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec()) 