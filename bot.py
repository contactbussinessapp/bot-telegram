import os, telebot, requests, csv, re, urllib.parse
from io import StringIO

# === CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

bot = telebot.TeleBot(TOKEN)
user_data = {}

def obtener_datos():
    try:
        r = requests.get(URL_SHEET, timeout=10)
        r.encoding = 'utf-8'
        # Limpiamos ruidos de formato y saltos de línea
        raw_text = r.text.replace('\r', '')
        return list(csv.reader(StringIO(raw_text)))
    except:
        return []

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
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSeleccioná tu región para buscar:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("r_"))
def set_region(call):
    region = call.data.split("_")[1]
    user_data[call.message.chat.id] = region
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"✅ Región *{region}* activada. ¿Qué buscás?")

@bot.message_handler(func=lambda message: True)
def buscar(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    region_user = user_data[uid]
    query = message.text.lower().strip()
    data = obtener_datos()
    
    if not data:
        bot.send_message(uid, "❌ Error al conectar con la base de datos.")
        return

    # --- DEFINICIÓN DE SEGMENTOS POR FILA ---
    # Python empieza en 0. Fila 2 (Excel) = Índice 1 (Python)
    bloque = []
    if region_user == "AR":
        bloque = data[1:97]    # Fila 2 a 97
    elif region_user == "CL":
        bloque = data[97:185]  # Fila 98 a 185
    elif region_user == "UY":
        bloque = data[185:186] # Fila 186
    elif region_user == "GLOBAL":
        # Incluye Fila 187 (AM-INT) y Fila 188 (GLOBAL)
        bloque = data[186:188]

    encontrados = []

    for fila in bloque:
        # Buscamos la palabra en toda la fila para que no se nos escape nada
        contenido_fila = " ".join(fila).lower()
        
        if query in contenido_fila:
            # Extraer link: buscamos algo que empiece con http en cualquier columna
            url_final = None
            for celda in fila:
                m = re.search(r'(https?://[^\s\n]+)', celda)
                if m:
                    url_final = m.group(0).strip()
                    break
            
            if url_final:
                # El nombre lo sacamos de la columna B o C (índices 1 o 2)
                # Limpiamos el nombre de links o basura
                nombre_crudo = fila[2] if len(fila) > 2 else fila[1]
                nombre = re.sub(r'https?://[^\s]+', '', nombre_crudo).strip()
                plataforma = fila[1].strip()
                
                encontrados.append(f"💎 *{plataforma}* - [{nombre}]({url_final})")

    if encontrados:
        # Eliminamos duplicados y mandamos la lista
        txt = f"🎯 *Resultados en {region_user}:*\n\n" + "\n".join(list(dict.fromkeys(encontrados))[:15])
        bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        # Si no hay nada en tu bloque, buscadores internacionales
        q_url = urllib.parse.quote(query)
        txt = f"❌ No encontré '{query}' en el radar local de {region_user}.\n\nPruebe búsqueda mundial:\n\n"
        txt += f"🛒 [Amazon](https://www.amazon.com/s?k={q_url}&tag=radarvip01-20)\n"
        txt += f"🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_c3MIbod9&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q_url})"
        bot.send_message(uid, txt, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
