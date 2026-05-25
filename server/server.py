from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STRING_POLACZENIA = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost\SQLEXPRESS01;' 
    r'DATABASE=PLC;' 
    r'Trusted_Connection=yes;'
)

class Raport(BaseModel):
    mac: str
    cpu: int
    gpu: int 
    network_mb: float

#1. ENDPOINT DLA AGENTA 
@app.post("/api/raport")
def przyjmij_raport(raport: Raport):
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        
        # Logika UPSERT (dodano needs_update do INSERT)
        zapytanie = """
        IF EXISTS (SELECT 1 FROM agents WHERE mac = ?)
            UPDATE agents SET cpu = ?, gpu = ?, network_mb = ?, ostatnia_aktualizacja = GETDATE() WHERE mac = ?
        ELSE
            INSERT INTO agents (mac, cpu, gpu, network_mb, is_locked, needs_update) VALUES (?, ?, ?, ?, 0, 0)
        """
        cursor.execute(zapytanie, (
            raport.mac, raport.cpu, raport.gpu, raport.network_mb, raport.mac,
            raport.mac, raport.cpu, raport.gpu, raport.network_mb
        ))
        
        # Pobieramy status blokady ORAZ status aktualizacji
        cursor.execute("SELECT is_locked, needs_update FROM agents WHERE mac = ?", raport.mac)
        status_row = cursor.fetchone()
        
        lock_status = bool(status_row[0]) if status_row else False
        update_status = bool(status_row[1]) if status_row else False
        
        # Zabezpieczenie OTA: Jeśli wysyłamy rozkaz aktualizacji, od razu go kasujemy z bazy,
        # żeby agent po restarcie nie pobierał się ponownie!
        if update_status:
            cursor.execute("UPDATE agents SET needs_update = 0 WHERE mac = ?", raport.mac)
        
        conn.commit()
        conn.close()
        
        # Odsyłamy dwa parametry do Agenta
        return {"status": "ok", "is_locked": lock_status, "needs_update": update_status}
    except Exception as e:
        return {"error": str(e)}

#2. ENDPOINT DLA DASHBOARDU
@app.get("/api/urzadzenia")
def pobierz_urzadzenia():
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        # Dodano pobieranie needs_update do panelu
        cursor.execute("SELECT mac, cpu, gpu, network_mb, is_locked, needs_update FROM agents")
        
        dane = []
        for row in cursor.fetchall():
            dane.append({
                "mac": row[0], "cpu": row[1], "gpu": row[2], 
                "network_mb": row[3], "is_locked": bool(row[4]), "needs_update": bool(row[5])
            })
        conn.close()
        return dane
    except:
        return []

#3. STEROWANIE BLOKADĄ
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

#4. NOWY ENDPOINT: WYMUSZENIE AKTUALIZACJI OTA
@app.post("/api/urzadzenia/{mac}/update")
def wymus_aktualizacje(mac: str):
    try:
        conn = pyodbc.connect(STRING_POLACZENIA)
        cursor = conn.cursor()
        # Ustawiamy flagę aktualizacji na 1
        cursor.execute("UPDATE agents SET needs_update = 1 WHERE mac = ?", mac)
        conn.commit()
        conn.close()
        return {"status": "update_scheduled"}
    except Exception as e:
        return {"error": str(e)}

#5. USUWANIE AGENTA
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