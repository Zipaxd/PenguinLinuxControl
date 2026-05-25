#!/bin/bash

# PenguinLinuxControl -Installer


echo "Rozpoczynam instalację Agenta "

# 1. Instalacja paczek systemowych
echo "📦 Pobieranie zależności (Python, Psutil, Requests)"
apt-get update -y > /dev/null
apt-get install -y python3 python3-requests python3-psutil curl > /dev/null

# 2. Tworzenie bezpiecznego folderu
echo "Przygotowywanie środowiska roboczego"
mkdir -p /root/PLC_Agent
cd /root/PLC_Agent

# 3. Pobranie kodu prosto z Twojego GitHuba
echo "⬇️ Pobieranie najnowszego Agenta z chmury"
curl -s -o agent.py https://raw.githubusercontent.com/Zipaxd/PenguinLinuxControl/main/agent.py

# 4. Tworzenie demona
echo "⚙️ Rejestrowanie Agenta w jądrze systemu..."
cat <<EOF > /etc/systemd/system/pingwin-agent.service
[Unit]
Description=Pingwin MDM Agent (Niezabijalny)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/PLC_Agent
ExecStart=/usr/bin/python3 /root/PLC_Agent/agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 5. Odpalenie Agenta na zawsze
echo "Uruchamianie procedur startowych"
systemctl daemon-reload
systemctl enable pingwin-agent.service
systemctl restart pingwin-agent.service

echo "Komputer został podpięty do systemu"