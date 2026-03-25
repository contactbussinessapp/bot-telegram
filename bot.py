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
    
    # OPORTUNIDADES AR (Filas 2 a 8)
    if region == "AR" and len(data) > 1:
        ofertas = data[1:8]
        msg = "🔥 *OPORTUNIDADES DEL DÍA EN AR* 🔥\n\n"
        for f in ofertas:
            if len(f) < 4: continue
            m = re.search(r'(https?://[^\s\n]+)', f[3])
            if m: msg += f"⚡ [{f[2]}]({m.group(0)}) - *{f[1]}*\n"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", disable_web_page_preview=True)

    # BIENVENIDA UY (Fila 186)
    elif region == "UY" and len(data) >= 186:
        f_uy = data[185] # Fila 186
        m = re.search(r'(https?://[^\s\n]+)', f_uy[3])
        if m:
            bot.send_message(call.message.chat.id, f"🇺🇾 *Bienvenido a Uruguay*\n\nVisitá nuestra tienda oficial:\n💎 [{f_uy[2]}]({m.group(0)})", parse_mode="Markdown")

    bot.send_message(call.message.chat.id, f"🔎 *¿Qué buscás en {region}?*", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def buscar(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    region = user_data[uid]
    query = message.text.lower().strip()
    data = obtener_datos()
    
    # Bloques exactos
    bloque = []
    if region == "AR": bloque = data[1:97]       # Fila 2 a 97
    elif region == "CL": bloque = data[97:185]   # Fila 98 a 185
    elif region == "UY": bloque = data[185:186]  # Fila 186 (Emidica)
    elif region == "GLOBAL": bloque = data[186:188]

    res = []
    for fila in bloque:
        if len(fila) < 4: continue
        if query in " ".join(fila).lower():
            m = re.search(r'(https?://[^\s\n]+)', fila[3])
            if m: res.append(f"💎 *{fila[1]}* - [{fila[2]}]({m.group(0)})")

    if res:
        bot.send_message(uid, f"🎯 *Resultados:* \n\n" + "\n".join(list(dict.fromkeys(res))), parse_mode="Markdown", disable_web_page_preview=True)
    else:
        # Failsafe con Amazon/Ali
        q = urllib.parse.quote(query)
        txt = f"❌ No encontré '{query}' en el radar local.\n\nPrueba aquí:\n\n"
        # Si es Uruguay, le recordamos Emidica por las dudas antes de ir a Amazon
        if region == "UY" and len(data) >= 186:
            m_uy = re.search(r'(https?://[^\s\n]+)', data[185][3])
            if m_uy: txt += f"🇺🇾 [Tienda Emidica Uruguay]({m_uy.group(0)})\n\n"
            
        txt += f"🛒 [Amazon](https://www.amazon.com/s?k={q}&tag=radarvip01-20)\n"
        txt += f"🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_c3MIbod9&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q})"
        bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
