import sqlite3
import os

DB_FILE = "presto.db"

def setup_initial_automat():
    """Funcție care creează baza de date și migrează datele vechi automat la prima rulare."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Crearea tabelelor dacă nu există
    c.execute('''CREATE TABLE IF NOT EXISTS livratori (nume TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS rapoarte (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operator TEXT,
                    comenzi INTEGER,
                    target REAL,
                    data_raport TEXT)''')
    
    # 2. Migrare automată livratori vechi
    if os.path.exists('contacte.txt'):
        with open('contacte.txt', 'r') as f:
            livratori = [l.strip() for l in f.readlines() if l.strip()]
        for nume in livratori:
            try:
                c.execute("INSERT OR IGNORE INTO livratori (nume) VALUES (?)", (nume,))
            except: pass
        # Redenumim fișierul text ca să nu mai fie citit data viitoare
        os.rename('contacte.txt', 'contacte_migrat.bak')
        
    # 3. Migrare automată rapoarte vechi
    DATA_DIR = "rapoarte_zilnice"
    if os.path.exists(DATA_DIR):
        fisiere = [f for f in os.listdir(DATA_DIR) if f.startswith("raport_")]
        for f_n in fisiere:
            cale_fisier = f"{DATA_DIR}/{f_n}"
            try:
                with open(cale_fisier, "r") as f:
                    op, com, tgt = f.read().strip().split('|')
                
                # Transformăm numele fișierului în dată formatată (YYYY-MM-DD)
                parti = f_n.split('_')
                data_raport = f"{parti[4]}-{parti[3]}-{parti[2]}" 
                
                # Inserăm în baza de date
                c.execute("INSERT INTO rapoarte (operator, comenzi, target, data_raport) VALUES (?, ?, ?, ?)",
                          (op, int(com), float(tgt), data_raport))
                
                # Ștergem fișierul text vechi după mutarea cu succes
                os.remove(cale_fisier)
            except: pass
            
        # Ștergem folderul dacă a rămas gol
        try:
            os.rmdir(DATA_DIR)
        except: pass

    conn.commit()
    conn.close()

# --- RULĂM CONFIGURAREA AUTOMATĂ ---
setup_initial_automat()
