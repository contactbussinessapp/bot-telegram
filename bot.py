import os, telebot, requests, csv, re, urllib.parse
from io import StringIO

TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

def obtener_datos():
    try:
        r = requests.get(URL_SHEET, timeout=10)
        r.encoding = 'utf-8'
        return list(csv.reader(StringIO(r.text.replace('\r', ''))))
    except: return []

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="r_AR"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="r_CL"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="r_UY"),
        telebot.types.InlineKeyboardButton("🌍 GLOBAL", callback_data="r_GLOBAL")
    ]
    markup.add(*btns)
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSeleccioná tu región:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("r_"))
def set_region(call):
    region = call.data.split("_")[1]
    user_data[call.message.chat.id] = region
    bot.answer_callback_query(call.id)
    
    data = obtener_datos()
    
    # --- LÓGICA DE OPORTUNIDADES DEL DÍA (SOLO AR) ---
    if region == "AR" and data:
        # Fila 2 a 8 (índices 1 a 7 en Python)
        ofertas_dia = data[1:8]
        msg_oportunidades = "🔥 *OPORTUNIDADES DEL DÍA EN AR* 🔥\n\n"
        
        for fila in ofertas_dia:
            if len(fila) < 4: continue
            # Buscador de link en columna D
            m = re.search(r'(https?://[^\s\n]+)', fila[3])
            url = m.group(0) if m else None
            if url:
                msg_oportunidades += f"⚡ [{fila[2]}]({url}) - *{fila[1]}*\n"
        
        bot.send_message(call.message.chat.id, msg_oportunidades, parse_mode="Markdown", disable_web_page_preview=True)

    bot.send_message(call.message.chat.id, f"🔎 *¿Qué más buscás en {region}?*", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def buscar(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    region_user = user_data[uid]
    query = message.text.lower().strip()
    data = obtener_datos()
    
    # Definición de bloques por filas
    bloque = []
    if region_user == "AR": bloque = data[1:97]
    elif region_user == "CL": bloque = data[97:185]
    elif region_user == "UY": bloque = data[185:186]
    elif region_user == "GLOBAL": bloque = data[186:188]

    encontrados = []
    for fila in bloque:
        texto_fila = " ".join(fila).lower()
        if query in texto_fila:
            m = re.search(r'(https?://[^\s\n]+)', fila[3])
            url = m.group(0) if m else None
            if url:
                encontrados.append(f"💎 *{fila[1]}* - [{fila[2]}]({url})")

    if encontrados:
        txt = f"🎯 *Resultados:* \n\n" + "\n".join(list(dict.fromkeys(encontrados))[:12])
    else:
        q = urllib.parse.quote(query)
        txt = f"❌ No hay resultados locales.\n\n🛒 [Amazon](https://www.amazon.com/s?k={q}&tag=radarvip01-20)\n🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_c3MIbod9&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q})"

    bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
