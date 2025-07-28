# AutomaticTelReader

Una applicazione desktop per la lettura automatica dei messaggi Telegram con interfaccia grafica sviluppata in Python.

## Descrizione

AutomaticTelReader è uno strumento che consente di monitorare e salvare automaticamente i messaggi ricevuti su Telegram. L'applicazione offre un'interfaccia grafica user-friendly per visualizzare messaggi, contatti e chat, con la possibilità di salvare anche le immagini ricevute.

## Caratteristiche Principali

- 🔐 **Login sicuro**: Autenticazione tramite API Telegram ufficiali
- 📱 **Monitoraggio in tempo reale**: Ricezione automatica di tutti i messaggi
- 💾 **Salvataggio persistente**: Conservazione di messaggi, contatti e immagini
- 🖼️ **Gestione immagini**: Visualizzazione e salvataggio delle immagini ricevute
- 👥 **Gestione contatti**: Visualizzazione dettagliata dei contatti salvati
- 💬 **Organizzazione chat**: Visualizzazione dei messaggi organizzati per chat
- 🗑️ **Pulizia cronologia**: Possibilità di eliminare la cronologia messaggi
- 🎨 **Interfaccia moderna**: Design pulito e intuitivo con PySide6

## Requisiti

- Python 3.7+
- PySide6 (Qt6 per Python)
- Telethon (client Telegram)

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/jeckoe/AutomaticTelReader.git
cd AutomaticTelReader
```

2. Installa le dipendenze:
```bash
pip install -r AutomaticTelReader/requirements.txt
```

3. Esegui l'applicazione:
```bash
python AutomaticTelReader/main.py
```

## Configurazione

Al primo avvio, l'applicazione richiederà:

1. **API ID**: Ottenibile da https://my.telegram.org/apps
2. **API Hash**: Fornito insieme all'API ID
3. **Numero di telefono**: Il tuo numero di telefono associato a Telegram

Le credenziali vengono salvate localmente nel file `config.json` (escluso dal versioning per sicurezza).

## Struttura del Progetto

```
AutomaticTelReader/
├── AutomaticTelReader/
│   ├── main.py              # File principale dell'applicazione
│   └── requirements.txt     # Dipendenze Python
├── .gitignore              # File da escludere dal versioning
└── README.md               # Documentazione (questo file)
```

### File di dati (generati automaticamente)

- `session.session`: File di sessione Telegram (escluso dal versioning)
- `config.json`: Configurazione utente (escluso dal versioning)
- `messages.json`: Cronologia messaggi salvati
- `contacts.json`: Database contatti
- `images.json`: Database immagini ricevute (codificate in base64)

## Utilizzo

### Avvio dell'applicazione

1. Avvia l'applicazione
2. Inserisci le credenziali API Telegram
3. Conferma il numero di telefono
4. L'applicazione inizierà automaticamente a monitorare i messaggi

### Funzionalità principali

- **Visualizzazione messaggi**: I messaggi ricevuti appaiono in tempo reale nella finestra principale
- **Gestione contatti**: Clicca su "Contatti" per visualizzare tutti i contatti salvati
- **Visualizzazione chat**: Clicca su "Chat" per vedere i messaggi organizzati per conversazione
- **Pulizia cronologia**: Usa "Elimina Cronologia" per cancellare tutti i dati salvati

## Sicurezza

⚠️ **Importante**: Questo strumento accede ai tuoi messaggi Telegram. Assicurati di:

- Utilizzarlo solo su dispositivi di fiducia
- Non condividere i file di sessione o configurazione
- Mantenere private le credenziali API
- Rispettare la privacy degli altri utenti

## Struttura del Codice

Il codice è organizzato in diverse classi principali:

### Classi UI
- `LoginWidget`: Gestisce l'interfaccia di login
- `MessagesWidget`: Finestra principale per visualizzare i messaggi
- `ContactsDialog`: Dialog per la gestione dei contatti
- `ChatsDialog`: Dialog per la visualizzazione delle chat
- `ImageDialog`: Dialog per la visualizzazione delle immagini

### Classi Core
- `MessageListener`: Thread per l'ascolto dei messaggi Telegram
- `MainApp`: Classe principale dell'applicazione

## Contribuire

Contributi, issue e feature request sono benvenuti! Sentiti libero di controllare la [issues page](https://github.com/jeckoe/AutomaticTelReader/issues).

## Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.

## Disclaimer

Questo strumento è fornito "così com'è" senza garanzie. L'uso è a proprio rischio e responsabilità. Assicurati di rispettare i termini di servizio di Telegram e le leggi locali sulla privacy.