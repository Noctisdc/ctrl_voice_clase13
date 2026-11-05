import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import paho.mqtt.client as paho
import json

# Configuración de la página
st.set_page_config(page_title="Control por Voz IoT", layout="wide", page_icon="🎙️")

# Estilos CSS profesionales idénticos al resto del portafolio
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
.stApp {
    background-color: #0f172a;
    background-image: radial-gradient(#1e3a5f 1.5px, transparent 1.5px);
    background-size: 26px 26px;
    font-family: 'Space Grotesk', sans-serif;
    color: #f8fafc;
}
.header-container {
    text-align: center;
    padding: 1.5rem 0;
    margin-bottom: 1.5rem;
}
.main-title {
    font-size: 3rem;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 0.5rem;
}
.sub-title {
    font-size: 1.2rem;
    color: #94a3b8;
    font-weight: 400;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(30, 41, 59, 0.85);
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 2rem;
}
.instruction-box {
    background: rgba(30, 41, 59, 0.95);
    border-left: 4px solid #38bdf8;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# Configuración MQTT usando WebSockets (Puerto 8000) para evitar bloqueos en la nube
BROKER = "broker.mqttdashboard.com"
PORT = 8000

def publicar_comando(frase):
    try:
        client = paho.Client(client_id="voice_client_web", transport="websockets")
        client.connect(BROKER, PORT)
        client.loop_start()
        
        mensaje = json.dumps({"Act1": frase})
        info = client.publish("voice_ctrl", mensaje)
        info.wait_for_publish(timeout=2.0)
        
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"Error de conexión MQTT: {e}")
        return False

# Encabezado de la app
st.markdown("""
<div class="header-container">
    <div class="main-title">🎙️ Control por Voz Multimodal</div>
    <div class="sub-title">Comandos de voz en tiempo real traducidos a acciones ciberfísicas vía MQTT</div>
</div>
""", unsafe_allow_html=True)

col_info, col_voice = st.columns(2, gap="large")

with col_info:
    with st.container(border=True):
        st.markdown("<h3 style='color: #38bdf8;'>💡 Comandos Reconocidos</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="instruction-box">
            <p><b>Para las luces (LED - Pin 2):</b></p>
            <ul>
                <li><code>"enciende las luces"</code></li>
                <li><code>"apaga las luces"</code></li>
            </ul>
            <p><b>Para la puerta (Servomotor - Pin 13):</b></p>
            <ul>
                <li><code>"abre la puerta"</code></li>
                <li><code>"Cierra la puerta"</code></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.info("💡 Haz clic en el botón de la derecha, concede permisos de micrófono a tu navegador y pronuncia claramente uno de los comandos.")

with col_voice:
    with st.container(border=True):
        st.markdown("<h3 style='color: #38bdf8; text-align: center;'>🗣️ Interfaz de Escucha</h3>", unsafe_allow_html=True)
        st.write("")
        st.write("Presiona el botón e inicia la captura de voz:")
        
        # Botón Bokeh para reconocimiento de voz del navegador
        stt_button = Button(label="🎙️ Iniciar Reconocimiento", width=250)
        
        stt_button.js_on_event("button_click", CustomJS(code="""
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = "es-ES";
         
            recognition.onresult = function (e) {
                var value = "";
                for (var i = e.resultIndex; i < e.results.length; ++i) {
                    if (e.results[i].isFinal) {
                        value += e.results[i][0].transcript;
                    }
                }
                if (value != "") {
                    document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
                }
            }
            recognition.start();
        """))

        result = streamlit_bokeh_events(
            stt_button,
            events="GET_TEXT",
            key="listen",
            refresh_on_update=False,
            override_height=75,
            debounce_time=0
        )

        if result:
            if "GET_TEXT" in result:
                texto_reconocido = result.get("GET_TEXT").strip().lower()
                st.markdown(f"**Texto detectado:** `{texto_reconocido}`")
                
                # Publicar el comando al broker MQTT
                if publicar_comando(texto_reconocido):
                    st.success(f"¡Comando '{texto_reconocido}' transmitido con éxito al circuito!")
