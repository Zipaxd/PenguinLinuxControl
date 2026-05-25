from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc

app = FastAPI()

# Pozwalamy Dashboardowi na rozmowę z API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Parametry połączenia z Twoją bazą SQLEXPRESS01
STRING_POLACZENIA = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost\SQLEXPRESS01;' 
    r'DATABASE=PLC;' 
    r'Trusted_Connection=yes;'
)

class Raport(BaseModel):
    mac: str
    cpu: int
    gpu: int # Tu przesyłasz RAM z Agenta
    network_mb: float

#1. ENDPOINT DLA AGENTA (Z OPTYMALIZACJĄ LOCKDOWNU)
@app.post("/api/raport")
def przyjmij_raport(raport: Raport):
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        
        # Logika UPSERT
        zapytanie = """
        IF EXISTS (SELECT 1 FROM agents WHERE mac = ?)
            UPDATE agents SET cpu = ?, gpu = ?, network_mb = ?, ostatnia_aktualizacja = GETDATE() WHERE mac = ?
        ELSE
            INSERT INTO agents (mac, cpu, gpu, network_mb, is_locked) VALUES (?, ?, ?, ?, 0)
        """
        cursor.execute(zapytanie, (
            raport.mac, raport.cpu, raport.gpu, raport.network_mb, raport.mac,
            raport.mac, raport.cpu, raport.gpu, raport.network_mb
        ))
        
        # Pobieramy aktualny status blokady, aby odesłać go Agentowi
        cursor.execute("SELECT is_locked FROM agents WHERE mac = ?", raport.mac)
        status_row = cursor.fetchone()
        lock_status = bool(status_row[0]) if status_row else False
        
        conn.commit()
        conn.close()
        return {"status": "ok", "is_locked": lock_status}
    except Exception as e:
        return {"error": str(e)}

#2. ENDPOINT DLA DASHBOARDU (LISTA AGENTÓW)
@app.get("/api/urzadzenia")
def pobierz_urzadzenia():
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        cursor.execute("SELECT mac, cpu, gpu, network_mb, is_locked FROM agents")
        
        dane = []
        for row in cursor.fetchall():
            dane.append({
                "mac": row[0], "cpu": row[1], "gpu": row[2], 
                "network_mb": row[3], "is_locked": bool(row[4])
            })
        conn.close()
        return dane
    except:
        return []

#3. STEROWANIE BLOKADĄ (Z PANELU)
@app.post("/api/urzadzenia/{mac}/lockdown")
def ustaw_lockdown(mac: str, status: int):
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        cursor.execute("UPDATE agents SET is_locked = ? WHERE mac = ?", status, mac)
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

#4. USUWANIE AGENTA Z PANELU ( ŻEBY NIE ZAŚMIECAŁO) 
@app.delete("/api/urzadzenia/{mac}")
def usun_agenta(mac: str):
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agents WHERE mac = ?", mac)
        conn.commit()
        conn.close()
        return {"status": "deleted"}
    except Exception as e:
        return {"error": str(e)}