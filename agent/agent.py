import os
import psutil
import requests
import time
import socket  

API_URL = "https://anyway-gravel-hydrogen.ngrok-free.dev/api/raport" 

# Agent sam zapyta Linuxa o jego nazwę
MOJ_MAC = socket.gethostname()

stan_blokady_lokalny = False

print(f"Agent [{MOJ_MAC}] uruchomiony...")

while True:
    try:
        # 1. Zbieranie telemetrii
        dane = {
            "mac": MOJ_MAC,
            "cpu": int(psutil.cpu_percent(interval=1)),
            "gpu": int(psutil.virtual_memory().percent), # Wysyłamy RAM w miejscu GPU
            "network_mb": round((psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv) / (1024*1024), 2)
        }
        
        # 2. Wysyłanie paczki do serwera
        odpowiedz = requests.post(API_URL, json=dane)
        server_response = odpowiedz.json()
        
        serwer_chce_lockdown = server_response.get("is_locked", False)

        # 3. LOGIKA BLOKOWANIA (LOCKDOWN)
        if serwer_chce_lockdown and not stan_blokady_lokalny:
            print("🚨 LOCKDOWN AKTYWOWANY! Zamykam środowisko graficzne i blokuję konta.")
            
            # Zablokowanie logowania dla zwykłych użytkowników (magiczny plik nologin)
            os.system('echo "URZĄDZENIE ZABLOKOWANE PRZEZ ADMINISTRATORA. ZWROĆ SPRZĘT." > /etc/nologin')
            
            # Zabezpieczenie przed cwany restartem (wstanie w czarnej konsoli)
            os.system("systemctl set-default multi-user.target") 
            
            # Ubicie obecnego pulpitu
            os.system("systemctl isolate multi-user.target")
            
            # Wylogowanie zalogowanych użytkowników
            os.system("for u in $(awk -F: '$3 >= 1000 {print $1}' /etc/passwd); do loginctl kill-user $u 2>/dev/null; done")
            
            stan_blokady_lokalny = True
            
        # 4. LOGIKA ODBLOKOWANIA
        elif not serwer_chce_lockdown and stan_blokady_lokalny:
            print("✅ LOCKDOWN ZDJĘTY! Przywracam dostęp.")
            
            # Usunięcie blokady logowania
            os.system("rm -f /etc/nologin")
            
            # Przywrócenie domyślnego ładowania okienek
            os.system("systemctl set-default graphical.target")
            
            # Włączenie okienek natychmiast
            os.system("systemctl isolate graphical.target")
            
            stan_blokady_lokalny = False

    except Exception as e:
        print(f"Błąd połączenia: {e}")

    # Agent czeka 5 sekund przed kolejnym uderzeniem do serwera
    time.sleep(5)