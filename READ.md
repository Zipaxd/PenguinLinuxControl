# PenguinLinuxControl

System MDM do zarządzania i blokowania stacji roboczych z systemem Linux. Projekt składa się z serwera centralnego, panelu webowego oraz agenta instalowanego na maszynach klienckich.

## Instalacja Agenta

Aby podłączyć nową maszynę do systemu, zaloguj się jako root i wykonaj poniższe polecenie w terminalu:

```bash
curl -s [https://raw.githubusercontent.com/Zipaxd/PenguinLinuxControl/main/install.sh](https://raw.githubusercontent.com/Zipaxd/PenguinLinuxControl/main/install.sh) | bash