import os
import telebot
import requests
import csv
import re
import urllib.parse
from io import StringIO

# === 1. CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
# Tu ID de Google Sheets real
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk' 
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

# Tus IDs de Afiliado (Se mantienen para búsquedas genéricas)
AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# === 2. TEXTOS MULTI-IDIOMA (Simplificado para el ejemplo, mantén los tuyos si prefieres) ===
TEXTS = {
    'es': {
        'configured': "✅ *Configurado para {name} {flag}*\n\n¿Qué estás buscando?",
        'searching': "🔍 *Escaneando secciones VIP...*",
        'results_for': "🎯 *Resultados para:* _{query}_\n\n",
        'no_results': "No encontré una oferta exacta en mis secciones, pero aquí tienes los mejores precios mundiales:\n"
    },
    'en': {
        'configured': "✅ *Set to {name} {flag}*\n\nWhat are you looking for?",
        'searching': "🔍 *Scanning VIP sections...*",
        'results_for': "🎯 *Results for:* _{query}_\n\n",
        'no_results': "I didn't find an exact VIP deal, but here are the best global prices:\n"
    }
}

# (Aquí puedes re-insertar todos tus diccionarios de idiomas que tenías antes)

COUNTRY_CONFIG = {
    'AR': {'name': 'Argentina', 'flag': '🇦🇷', 'lang': 'es'},
    'CL': {'name': 'Chile', 'flag': '🇨🇱', 'lang': 'es'},
    'UY': {'name': 'Uruguay', 'flag': '🇺🇾', 'lang': 'es'},
    'GLOBAL': {'name': 'Global', 'flag': '🌍', 'lang': 'en'}
    # Agrega el resto de países igual que los tenías...
}

# === 3. FUNCIÓN DE LECTURA DE EXCEL ===
def get_sheet_data():
    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        return list(csv.reader(StringIO(r.text)))
    except Exception as e:
        print(f"Error Sheets: {e}")
        return []

# === 4. COMANDOS Y SELECCIÓN DE PAÍS ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Botones rápidos
    markup.row(
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="set_AR"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="set_CL"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="set_UY")
    )
    markup.row(telebot.types.InlineKeyboardButton("🌍 GLOBAL", callback_data="set_GLOBAL"))
    bot.reply_to(message, "🌍 *SELECT YOUR COUNTRY / SELECCIONA TU PAÍS*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais_code = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais_code}
    config = COUNTRY_CONFIG.get(pais_code, COUNTRY_CONFIG['GLOBAL'])
    t = TEXTS.get(config['lang'], TEXTS['en'])
    msg = t['configured'].format(name=config['name'], flag=config['flag'])
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# === 5. MOTOR DE BÚSQUEDA INTELIGENTE ===
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return send_welcome(message)

    pais_user = user_data[chat_id]['pais']
    lang = COUNTRY_CONFIG[pais_user]['lang']
    t = TEXTS.get(lang, TEXTS['en'])
    
    query = message.text.lower().strip()
    msg_espera = bot.send_message(chat_id, t['searching'], parse_mode="Markdown")
    
    csv_data = get_sheet_data()
    res_p1 = [] # Prioridad 1 (Tuyo/Emidica)
    res_p2 = [] # Prioridad 2 (Afiliados)

    for fila in csv_data:
        if len(fila) < 5: continue
        
        iso_excel = fila[0].strip().upper()
        seccion_nombre = fila[1].strip().lower()
        plataforma = fila[2].strip()
        link = fila[3].strip()
        prioridad = fila[4].strip()

        # Si el país coincide o es global
        if iso_excel == pais_user or iso_excel == "GLOBAL":
            if query in seccion_nombre:
                # Formato: [Plataforma] Nombre (Prioridad)
                txt = f"💎 *{plataforma}* - [{fila[1]}]({link})"
                if prioridad == "1":
                    res_p1.append(txt)
                else:
                    res_p2.append(txt)

    # Respuesta Final
    final_msg = t['results_for'].format(query=query)
    
    if res_p1:
        final_msg += "🔥 *OFERTAS VIP PRIORITARIAS:*\n" + "\n".join(res_p1) + "\n\n"
    
    if res_p2:
        final_msg += "🌐 *OTRAS SECCIONES RECOMENDADAS:*\n" + "\n".join(res_p2) + "\n\n"

    # Si no hay nada en el Excel, usamos los buscadores globales
    if not res_p1 and not res_p2:
        final_msg += t['no_results']
        q_url = urllib.parse.quote(query)
        final_msg += f"🛒 [Buscar en Amazon](https://www.amazon.com/s?k={q_url}&tag={AMAZON_TAG})\n"
        final_msg += f"🛍️ [Buscar en AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q_url})"

    bot.edit_message_text(final_msg, chat_id, msg_espera.message_id, parse_mode="Markdown", disable_web_page_preview=True)

# === 6. EJECUCIÓN ===
if __name__ == "__main__":
    print("🚀 RADAR VIP GLOBAL OPERATIVO...")
    bot.polling(none_stop=True)
