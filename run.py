#!/usr/bin/env python3
"""
AutomaticTelReader - Punto di ingresso principale

Script di avvio per l'applicazione AutomaticTelReader.
Questo file può essere eseguito direttamente per avviare l'applicazione.
"""

import sys
import os

# Aggiunge il percorso del modulo principale al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AutomaticTelReader'))

# Importa ed esegue l'applicazione principale
from main import MainApp

if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec())