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
a0a1a;color:#fff;min-height:100vh;padding:20px 16px 40px;max-width:480px;margin:0 auto}
.header{text-align:center;padding:24px 0 20px}
.logo{font-size:2rem;margin-bottom:4px}
.title{font-size:1.6rem;font-weight:700;color:#fff}
.subtitle{font-size:.85rem;color:#888;margin-top:4px}
.status-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 16px;border-radius:20px;font-size:.8rem;font-weight:600;margin-top:12px}
.badge-ok{background:#0d2b1a;color:#2ecc71;border:1px solid #2ecc71}
.badge-degradado{background:#2b1a0d;color:#e67e22;border:1px solid #e67e22}
.badge-medindo{background:#1a1a2b;color:#3498db;border:1px solid #3498db}
.badge-erro{background:#2b0d0d;color:#e74c3c;border:1px solid #e74c3c}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:20px 0}
.card{background:#12122a;border-radius:16px;padding:20px 16px;text-align:center;border:1px solid #1e1e3a}
.card.ping-card{grid-column:1/-1;padding:16px}
.card-icon{font-size:1.6rem;margin-bottom:8px}
.card-label{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:1px}
.card-value{font-size:2.2rem;font-weight:800;color:#fff;line-height:1.1;margin:6px 0 2px}
.card-unit{font-size:.8rem;color:#666}
.bar-wrap{background:#1e1e3a;border-radius:8px;height:8px;margin-top:10px;overflow:hidden}
.bar{height:100%;border-radius:8px;transition:width .8s ease;width:0%}
.bar-dl{background:linear-gradient(90deg,#3498db,#2ecc71)}
.bar-ul{background:linear-gradient(90deg,#9b59b6,#3498db)}
.btn-medir{width:100%;padding:18px;background:linear-gradient(135deg,#3498db,#2ecc71);border:none;border-radius:16px;color:#fff;font-size:1.1rem;font-weight:700;cursor:pointer;letter-spacing:.5px;transition:opacity .2s,transform .1s;margin-bottom:24px}
.btn-medir:active{transform:scale(.97);opacity:.9}
.btn-medir:disabled{opacity:.5;cursor:not-allowed}
.chart-box{background:#12122a;border-radius:16px;padding:16px;border:1px solid #1e1e3a;margin-bottom:20px}
.chart-title{font-size:.85rem;color:#888;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px}
.historico{background:#12122a;border-radius:16px;border:1px solid #1e1e3a;overflow:hidden;margin-bottom:20px}
.historico-title{padding:14px 16px;font-size:.85rem;color:#888;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #1e1e3a}
.historico-item{display:
flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #0f0f22;font-size:.9rem}
.historico-item:last-child{border-bottom:none}
.hist-time{color:#888;font-size:.8rem}
.hist-vals{display:flex;gap:12px}
.hist-dl{color:#2ecc71;font-weight:600}
.hist-ul{color:#3498db;font-weight:600}
.hist-ping{color:#f39c12;font-size:.8rem}
.hist-badge{font-size:.7rem;padding:2px 8px;border-radius:10px}
.hist-ok{background:#0d2b1a;color:#2ecc71}
.hist-deg{background:#2b1a0d;color:#e67e22}
.hist-erro{background:#2b0d0d;color:#e74c3c}
.alerta-box{background:#2b1a0d;border:1px solid #e67e22;border-radius:12px;padding:14px 16px;margin-bottom:16px;font-size:.9rem;color:#e67e22;display:none}
.footer{text-align:center;color:#444;font-size:.75rem;padding-top:8px}
</style>
</head>
<body>
<div class="header">
<div class="logo">⚡</div>
<div class="title">Internet Power</div>
<div class="subtitle">Monitor inteligente de rede</div>
<span class="status-badge badge-medindo" id="badge">● Aguardando medição</span>
</div>
<div id="alerta-box" class="alerta-box"></div>
<div class="cards">
<div class="card">
<div class="card-icon">📥</div>
<div class="card-label">Download</div>
<div class="card-value" id="dl">--</div>
<div class="card-unit">Mbps</div>
<div class="bar-wrap"><div class="bar bar-dl" id="bar-dl"></div></div>
</div>
<div class="card">
<div class="card-icon">📤</div>
<div class="card-label">Upload</div>
<div class="card-value" id="ul">--</div>
<div class="card-unit">Mbps</div>
<div class="bar-wrap"><div class="bar bar-ul" id="bar-ul"></div></div>
</div>
<div class="card ping-card">
<div style="display:flex;justify-content:space-between;align-items:center">
<div>
<div class="card-icon">🏓</div>
<div class="card-label">Ping</div>
<div class="card-value" id="ping" style="font-size:1.6rem">--</div>
<div class="card-unit">ms</div>
</div>
<div style="text-align:right">
<div class="card-label">Última medição</div>
<div id="ultimo-tempo" style="font-size:1.2rem;font-weight:700;color:#888">--:--:--</div>
<div class="card-label" style="margin-top:8px">Próxima em</div>
<div id="countdown" style="font-size:1.2rem;font-weight:700;color:#3498db">5:00</div>
</div>
</div>
</div>
</div>
<button class="btn-medir" id="btn" onclick="medirAgora()">🔍 MEDIR AGORA</button>
<div class="chart-box">
<div class="chart-title">📈 Histórico de velocidade</div>
<canvas id="grafico" height="120"></canvas>
</div>
<div class="historico">
<div class="historico-title">📋 Medições recentes</div>
<div id="lista-historico"></div>
</div>
<div class="footer">Internet Power v1.0 — Atualização automática a cada 5 min</div>
<script>
const socket=io();
let labels=[],dlData=[],ulData=[],countdown=300,timer;
const ctx=document.getElementById('grafico').getContext('2d');
const chart=new Chart(ctx,{type:'line',data:{labels:labels,datasets:[{label:'Download',data:dlData,borderColor:'#2ecc71',backgroundColor:'rgba(46,204,113,0.08)',tension:0.4,fill:true,pointRadius:4},{label:'Upload',data:ulData,borderColor:'#3498db',backgroundColor:'rgba(52,152,219,0.08)',tension:0.4,fill:true,pointRadius:4}]},options:{responsive:true,plugins:{legend:{labels:{color:'#888',font:{size:11}}}},scales:{x:{ticks:{color:'#666',font:{size:10}},grid:{color:'#1e1e3a'}},y:{ticks:{color:'#666',font:{size:10}},grid:{color:'#1e1e3a'}}}}});
socket.on('nova_medicao',function(d){
document.getElementById('dl').textContent=d.download_mbps;
document.getElementById('ul').textContent=d.upload_mbps;
document.getElementById('ping').textContent=d.ping_ms;
document.getElementById('ultimo-tempo').textContent=d.timestamp;
const maxMbps=200;
document.getElementById('bar-dl').style.width=Math.min((d.download_mbps/maxMbps)*100,100)+'%';
document.getElementById('bar-ul').style.width=Math.min((d.upload_mbps/maxMbps)*100,100)+'%';
const badge=document.getElementById('badge');
if(d.status==='ok'){badge.className='status-badge badge-ok';badge.textContent='● Rede estável';}
else if(d.status==='degradado'){badge.className='status-badge badge-degradado';badge.textContent='● Sinal degradado';}
else if(d.status==='erro'){badge.className='status-badge badge-erro';badge.textContent='● Erro na medição';}
const alertaBox=document.getElementById('alerta-box');
if(d.alerta){alertaBox.style.display='block';alertaBox.textContent=d.alerta;}
else{alertaBox.style.display='none';}
labels.push(d.timestamp);dlData.push(d.download_mbps);ulData.push(d.upload_mbps);
if(labels.length>10){labels.shift();dlData.shift();ulData.shift();}
chart.update();
const lista=document.getElementById('lista-historico');
const badgeClass=d.status==='ok'?'hist-ok':d.status==='degradado'?'hist-deg':'hist-erro';
const badgeText=d.status==='ok'?'✅ Estável':d.status==='degradado'?'⚠️ Queda':'❌ Erro';
const item=document.createElement('div');
item.className='historico-item';
item.innerHTML=`<span class="hist-time">${d.timestamp}</span><div class="hist-vals"><span class="hist-dl">↓${d.download_mbps}</span><span class="hist-ul">↑${d.upload_mbps}</span><span class="hist-ping">${d.ping_ms}ms</span></div><span class="hist-badge ${badgeClass}">${badgeText}</span>`;
lista.insertBefore(item,lista.firstChild);
if(lista.children.length>10)lista.removeChild(lista.lastChild);
const btn=document.getElementById('btn');
btn.disabled=false;
btn.textContent='🔍 MEDIR AGORA';
reiniciarCountdown();
});
function reiniciarCountdown(){
clearInterval(timer);countdown=300;
timer=setInterval(()=>{countdown--;const m=Math.floor(countdown/60);const s=countdown%60;document.getElementById('countdown').textContent=m+':'+String(s).padStart(2,'0');if(countdown<=0)clearInterval(timer);},1000);
}
function medirAgora(){
const btn=document.getElementById('btn');
btn.disabled=true;btn.textContent='⏳ Medindo...';
const badge=document.getElementById('badge');
badge.className='status-badge badge-medindo';
badge.textContent='● Medindo agora...';
fetch('/medir');
}
reiniciarCountdown();
</script>
</body>
</html>"""
@app.route("/medir")
def medir_agora():
threading.Thread(target=medir_velocidade).start()
return "ok"
@app.route("/manifest.json")
def manifest():
return {
"name": "Internet Power",
"short_name": "InternetPower",
"description": "Monitor inteligente de rede",
"start_url": "/",
"display": "standalone",
"background_color": "#0a0a1a",
"theme_color": "#0a0a1a",
"icons": [{"src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/26a1.png","sizes": "72x72","type": "image/png"}]
}
if __name__ == "__main__":
thread = threading.Thread(target=loop_monitoramento, daemon=True)
thread.start()
port = int(os.environ.get("PORT", 5000))
print(f"\n⚡ Internet Power iniciado!")
print(f"🌐 Acesse: http://localhost:{port}\n")
socketio.run(app, host="0.0.0.0", port=port, debug=False)
Depois de colar clique em "Commit changes" para salvar.
Me confirma quando salvar que vamos fazer o redeploy no Railway! 🚀
