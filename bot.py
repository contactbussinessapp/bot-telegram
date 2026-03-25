import os
import telebot
import requests
import csv
import urllib.parse
from io import StringIO

# ==========================================
# 1. CONFIGURACIÓN (SIMPLE Y DIRECTA)
# ==========================================
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

# Tus IDs de Afiliado para búsquedas cuando no hay coincidencia exacta
AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ==========================================
# 2. FUNCIÓN DE LECTURA DE BASE DE DATOS
# ==========================================
def obtener_datos_excel():
    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        # Convertimos el CSV en una lista para procesar
        return list(csv.reader(StringIO(r.text)))
    except Exception as e:
        print(f"Error al leer Excel: {e}")
        return []

# ==========================================
# 3. COMANDOS DE INICIO Y PAÍS
# ==========================================
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
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSelecciona tu país para rastrear ofertas:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def callback_pais(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = pais
    bot.edit_message_text(f"✅ Configurado para *{pais}*.\n¿Qué producto estás buscando hoy?", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ==========================================
# 4. MOTOR DE BÚSQUEDA Y PRIORIDADES
# ==========================================
@bot.message_handler(func=lambda message: True)
def buscar(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return welcome(message)

    pais_user = user_data[chat_id]
    query = message.text.lower().strip()
    
    msg_espera = bot.send_message(chat_id, "🔍 *Escaneando secciones VIP...*", parse_mode="Markdown")
    
    excel_data = obtener_datos_excel()
    p1 = [] # Prioridad 1 (Tuyo / Emidica / Dropshipping)
    p2 = [] # Prioridad 2 (Afiliados locales)

    # El bot recorre el Excel buscando coincidencias
    for fila in excel_data:
        if len(fila) < 4: continue
        
        iso_excel = fila[0].strip().upper()
        nombre_item = fila[1].strip().lower()
        plataforma = fila[2].strip()
        url = fila[3].strip()
        # La prioridad suele estar en la columna 5 (índice 4)
        prioridad = fila[4].strip() if len(fila) > 4 else "2"

        # Si el país coincide o es una oferta global
        if iso_excel == pais_user or iso_excel == "GLOBAL":
            # Si el término de búsqueda está en el nombre de la sección/producto
            if query in nombre_item:
                link_txt = f"💎 *{plataforma}* - [{fila[1].strip()}]({url})"
                if prioridad == "1":
                    p1.append(link_txt)
                else:
                    p2.append(link_txt)

    # CONSTRUCCIÓN DE LA RESPUESTA FINAL
    respuesta = f"🎯 *Resultados para:* _{query}_\n\n"
    
    if p1:
        respuesta += "🔥 *OFERTAS VIP PRIORITARIAS:*\n" + "\n".join(p1) + "\n\n"
    
    if p2:
        respuesta += "🌐 *SECCIONES RECOMENDADAS:*\n" + "\n".join(p2) + "\n\n"

    # Si el Excel no tiene nada específico, activamos los buscadores mundiales
    if not p1 and not p2:
        q_clean = urllib.parse.quote(query)
        respuesta += "No hay una sección exacta en el radar, pero aquí tienes los mejores precios:\n\n"
        respuesta += f"🛒 [Buscar en Amazon](https://www.amazon.com/s?k={q_clean}&tag={AMAZON_TAG})\n"
        respuesta += f"🛍️ [Buscar en AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q_clean})"

    bot.edit_message_text(respuesta, chat_id, msg_espera.message_id, parse_mode="Markdown", disable_web_page_preview=True)

# ==========================================
# 5. LANZAMIENTO SEGURO
# ==========================================
if __name__ == "__main__":
    # Limpiamos cualquier rastro anterior en la API de Telegram
    bot.remove_webhook()
    print("🔥 RADAR VIP GLOBAL ESTÁ EN LÍNEA...")
    bot.polling(none_stop=True)
