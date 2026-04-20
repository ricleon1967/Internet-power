import os
import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask_socketio import SocketIO
import speedtest
import threading
import time
from datetime import datetime
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
historico = []
def medir_velocidade():
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Medindo...")
try:
st = speedtest.Speedtest()
st.get_best_server()
download = round(st.download() / 1_000_000, 2)
upload = round(st.upload() / 1_000_000, 2)
ping = round(st.results.ping, 2)
status = "ok"
alerta = None
if historico:
ultima = historico[-1]
queda = ultima["download_mbps"] - download
if queda > ultima["download_mbps"] * 0.30:
status = "degradado"
alerta = f"Queda de {round(queda,1)} Mbps detectada!"
resultado = {
"timestamp" : datetime.now().strftime("%H:%M:%S"),
"download_mbps" : download,
"upload_mbps" : upload,
"ping_ms" : ping,
"status" : status,
"alerta" : alerta
}
historico.append(resultado)
if len(historico) > 20:
historico.pop(0)
socketio.emit("nova_medicao", resultado)
print(f"Download: {download} Mbps | Upload: {upload} Mbps | Ping: {ping} ms")
except Exception as e:
erro = {"timestamp": datetime.now().strftime("%H:%M:%S"),
"download_mbps": 0, "upload_mbps": 0, "ping_ms": 0,
"status": "erro", "alerta": f"Erro: {str(e)}"}
historico.append(erro)
socketio.emit("nova_medicao", erro)
print(f"Erro: {e}")
def loop_monitoramento():
medir_velocidade()
import schedule
schedule.every(5).minutes.do(medir_velocidade)
while True:
schedule.run_pending()
time.sleep(1)
@app.route("/")
def index():
return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0a0a1a">
<title>Internet Power</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0
