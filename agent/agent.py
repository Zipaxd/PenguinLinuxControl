import os
import sys
import time
import socket
import psutil
import requests

# Adres serwera API (zaktualizuj, jeśli zmienił się link w Ngroku)
API_URL = "https://anyway-gravel-hydrogen.ngrok-free.dev/api/raport"

# Automatyczne pobieranie nazwy komputera jako unikalnego identyfikatora
MOJ_MAC = socket.gethostname()

stan_blokady_lokalny = False

print(f"Agent [{MOJ_MAC}] uruchomiony...")

while True:
    try:
        # 1. Zbieranie danych telemetrycznych z systemu
        dane = {
            "mac": MOJ_MAC,
            "cpu": int(psutil.cpu_percent(interval=1)),
            "gpu": int(psutil.virtual_memory().percent),  # Wysyłamy zużycie RAM w miejsce GPU
            "network_mb": round((psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv) / (1024 * 1024), 2)
        }
        
        # 2. Wysyłanie raportu telemetrycznego do serwera
        odpowiedz = requests.post(API_URL, json=dane, timeout=5)
        server_response = odpowiedz.json()
        
        serwer_chce_lockdown = server_response.get("is_locked", False)
        serwer_chce_update = server_response.get("needs_update", False)

        # 3. Logika automatycznej aktualizacji (OTA)
        if serwer_chce_update:
            print("Otrzymano rozkaz aktualizacji. Pobieranie nowej wersji z GitHuba...")
            
            # Nadpisanie obecnego pliku nowym kodem z repozytorium
            os.system("wget -q -O /root/PLC_Agent/agent.py https://raw.githubusercontent.com/Zipaxd/PenguinLinuxControl/main/agent/agent.py")
            
            print("Aktualizacja pobrana. Wykonuję twardy restart usługi...")
            # Zamknięcie skryptu. Systemd automatycznie podniesie go na nowo z nowym kodem
            sys.exit(0)

        # 4. Logika blokowania komputera (Lockdown)
        if serwer_chce_lockdown and not stan_blokady_lokalny:
            print("🚨 LOCKDOWN AKTYWOWANY! Zamykam środowisko graficzne.")
            
            # Włączenie systemowej blokady logowania
            os.system('echo "URZADZENIE ZABLOKOWANE PRZEZ ADMINISTRATORA. ZWROC SPRZET." > /etc/nologin')
            
            # Zmiana domyślnego trybu uruchamiania na konsolowy (zabezpieczenie przed restartem)
            os.system("systemctl set-default multi-user.target")
            
            # Przełączenie systemu w tryb konsoli (ubicie pulpitu)
            os.system("systemctl isolate multi-user.target")
            
            # Wylogowanie wszystkich zalogowanych użytkowników zwykłych (UID >= 1000)
            os.system("for u in $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do loginctl kill-user $u 2>/dev/null; done")
            
            stan_blokady_lokalny = True
            
        # 5. Logika odblokowania komputera
        elif not serwer_chce_lockdown and stan_blokady_lokalny:
            print("✅ LOCKDOWN ZDJĘTY! Przywracam dostęp do systemu.")
            
            # Usunięcie blokady logowania
            os.system("rm -f /etc/nologin")
            
            # Przywrócenie domyślnego uruchamiania w trybie graficznym
            os.system("systemctl set-default graphical.target")
            
            # Natychmiastowe odpalenie środowiska graficznego
            os.system("systemctl isolate graphical.target")
            
            stan_blokady_lokalny = False

    except Exception as e:
        print(f"Blad polaczenia lub wykonania: {e}")

    # Odstęp czasowy między raportami (5 sekund)
    time.sleep(5)