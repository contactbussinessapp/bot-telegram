import os, telebot, requests, csv, re, urllib.parse
from io import StringIO

# === CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

def obtener_datos():
    try:
        r = requests.get(URL_SHEET, timeout=10)
        r.encoding = 'utf-8'
        # Limpieza de retornos de carro para evitar filas vacías
        return list(csv.reader(StringIO(r.text.replace('\r', ''))))
    except:
        return []

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="s_AR"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="s_UY"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="s_CL")
    ]
    markup.add(*btns)
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSeleccioná tu país:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("s_"))
def set_p(call):
    user_data[call.message.chat.id] = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🔎 *¿Qué buscás hoy?*")

@bot.message_handler(func=lambda message: True)
def buscar(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    pais = user_data[uid]
    busqueda = message.text.lower().strip()
    data = obtener_datos()
    res = []

    for fila in data:
        # Estructura Nueva: 
        # A=0(País), B=1(Plataforma), C=2(Producto), D=3(Link), E=4(Prioridad)
        if len(fila) < 4: continue
        
        iso = fila[0].strip().upper()
        plataforma = fila[1].strip()
        producto = fila[2].strip()
        link_celda = fila[3].strip()
        prioridad = fila[4].strip() if len(fila) > 4 else "2"

        if iso == pais or iso == "GLOBAL":
            # Buscamos la palabra clave en el Producto o la Plataforma
            if busqueda in producto.lower() or busqueda in plataforma.lower():
                
                # Extraemos la URL pura de la columna D (evita errores con texto extra)
                match_url = re.search(r'(https?://[^\s\n]+)', link_celda)
                url_final = match_url.group(0) if match_url else None
                
                if url_final:
                    # Icono según prioridad en columna E
                    prio_icon = "🔥" if "1" in prioridad else "💎"
                    res.append(f"{prio_icon} *{plataforma}* - [{producto}]({url_final})")

    if res:
        # Eliminamos duplicados y limitamos resultados
        final_res = list(dict.fromkeys(res))[:10]
        bot.send_message(uid, f"🎯 *Resultados para:* _{busqueda}_\n\n" + "\n".join(final_res), 
                         parse_mode="Markdown", disable_web_page_preview=True)
    else:
        # Si no hay local, búsqueda automática en Amazon/Ali
        q = urllib.parse.quote(busqueda)
        txt = f"❌ No hay resultados locales para '{busqueda}'.\n\nPrueba búsqueda mundial:\n\n"
        txt += f"🛒 [Amazon](https://www.amazon.com/s?k={q}&tag={AMAZON_TAG})\n"
        txt += f"🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q})"
        bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
