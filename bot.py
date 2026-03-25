import os
import telebot
import requests
import csv
import urllib.parse
import re
from io import StringIO

# === 1. CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# === 2. DICCIONARIO DE SINÓNIMOS (ADAPTACIÓN REGIONAL) ===
# Esto permite que si buscan "chata", el bot entienda que es "auto/camioneta"
SINONIMOS = {
    "auto": ["carro", "coche", "automovil", "chata", "camioneta", "troca", "vehiculo", "nave"],
    "bici": ["bicicleta", "cicla", "chiva", "btt", "mountain bike"],
    "celu": ["telefono", "celular", "smartphone", "movil", "iphone", "android"],
    "compu": ["computadora", "ordenador", "laptop", "notebook", "pc"],
    "ropa": ["indumentaria", "vestimenta", "pilcha", "trapo", "prenda"]
}

def normalizar_busqueda(texto):
    texto = texto.lower().strip()
    # Si el usuario usa un modismo, lo traducimos a la palabra clave del Excel
    for clave, variaciones in SINONIMOS.items():
        if texto in variaciones or any(v in texto for v in variaciones):
            return clave
    return texto

# === 3. FUNCIÓN DE LECTURA ===
def obtener_datos():
    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        return list(csv.reader(StringIO(r.text.replace('\r', ''))))
    except:
        return []

# === 4. COMANDOS DE INICIO ===
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="set_AR"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="set_UY"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="set_CL"),
        telebot.types.InlineKeyboardButton("🌍 GLOBAL", callback_data="set_GLOBAL")
    ]
    markup.add(*btns)
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\n¿Desde dónde nos escribís, paisano?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def callback_pais(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = pais
    bot.edit_message_text(f"✅ *{pais}* activado. ¡Mandale sin miedo! ¿Qué estás buscando?", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# === 5. MOTOR DE BÚSQUEDA ADAPTATIVO ===
@bot.message_handler(func=lambda message: True)
def buscar(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return welcome(message)

    pais_user = user_data[chat_id]
    entrada_usuario = message.text.lower().strip()
    query_raiz = normalizar_busqueda(entrada_usuario)
    
    bot.send_chat_action(chat_id, 'typing')
    excel_data = obtener_datos()
    
    resultados_vip = []
    resultados_otros = []

    for fila in excel_data:
        if len(fila) < 4: continue
        
        # Datos del Excel (limpios de espacios)
        iso = fila[0].strip().upper()
        nombre_seccion = fila[1].strip()
        plataforma = fila[2].strip()
        link = fila[3].strip()
        prioridad = fila[4].strip() if len(fila) > 4 else "2"

        if iso == pais_user or iso == "GLOBAL":
            # Buscamos si la raíz de la búsqueda está en el nombre del Excel
            if query_raiz in nombre_seccion.lower() or entrada_usuario in nombre_seccion.lower():
                item = f"💎 *{plataforma}* - [{nombre_seccion}]({link})"
                if "1" in prioridad:
                    resultados_vip.append(item)
                else:
                    resultados_otros.append(item)

    # RESPUESTA FINAL
    if resultados_vip or resultados_otros:
        res = f"🎯 *Radar para:* _{entrada_usuario}_\n\n"
        if resultados_vip:
            res += "🔥 *OFERTAS TOP:*\n" + "\n".join(resultados_vip) + "\n\n"
        if resultados_otros:
            res += "🌐 *MÁS OPCIONES:*\n" + "\n".join(resultados_otros)
    else:
        # Si no hay nada, mandamos a los buscadores con la palabra original
        q_url = urllib.parse.quote(entrada_usuario)
        res = f"🎯 No encontré '{entrada_usuario}' en el radar local, pero chequeá estos precios mundiales:\n\n"
        res += f"🛒 [Amazon Global](https://www.amazon.com/s?k={q_url}&tag={AMAZON_TAG})\n"
        res += f"🛍️ [AliExpress Ofertas](https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q_url})"

    bot.send_message(chat_id, res, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
