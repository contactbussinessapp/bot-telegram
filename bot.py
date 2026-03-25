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
        return list(csv.reader(StringIO(r.text)))
    except: return []

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="s_AR"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="s_UY"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="s_CL")
    ]
    markup.add(*btns)
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSeleccioná tu país, paisano:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("s_"))
def set_p(call):
    user_data[call.message.chat.id] = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🔎 *¿Qué estás buscando?* (ej: autos, bicis, pescar)", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def buscar(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    pais = user_data[uid]
    busqueda = message.text.lower().strip()
    data = obtener_datos()
    res = []

    for fila in data:
        # Unificamos la fila y limpiamos saltos de línea para buscar bien
        texto_fila = " ".join(fila).lower().replace('\n', ' ')
        iso_fila = fila[0].strip().upper()

        if (iso_fila == pais or iso_fila == "GLOBAL") and busqueda in texto_fila:
            # Extraer el link limpio
            link = None
            for celda in fila:
                m = re.search(r'(https?://[^\s\n]+)', celda)
                if m: 
                    link = m.group(0)
                    break
            
            if link:
                # Prioridad 1 tiene emoji de fuego
                prio = "🔥" if "1" in " ".join(fila[4:]) else "💎"
                
                # LIMPIEZA DEL NOMBRE:
                # Tomamos la columna 1, le sacamos los saltos de línea y el link si está ahí metido
                nombre_sucio = fila[1].replace('\n', ' ').strip()
                nombre_limpio = re.sub(r'https?://[^\s]+', '', nombre_sucio).strip()
                # Si el nombre quedó vacío o muy corto, usamos la plataforma (columna 2)
                if len(nombre_limpio) < 3 and len(fila) > 2:
                    nombre_limpio = fila[2].strip()

                res.append(f"{prio} [{nombre_limpio}]({link})")

    if res:
        # Quitamos duplicados y armamos lista limpia
        final_list = list(dict.fromkeys(res))[:12]
        txt = f"🎯 *Resultados para:* _{busqueda}_\n\n" + "\n".join(final_list)
    else:
        q = urllib.parse.quote(busqueda)
        txt = f"❌ No encontré '{busqueda}' en el radar local.\n\nPrueba en los mercados mundiales:\n\n"
        txt += f"🛒 [Amazon Global](https://www.amazon.com/s?k={q}&tag=radarvip01-20)\n"
        txt += f"🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_c3MIbod9&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q})"

    bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
