import os
import telebot
import requests
import csv
import urllib.parse
import re
from io import StringIO

# === CONFIGURACIÓN ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1zGZF5meVfgRZvRLSvKGelwYs2h3pgA7YEpC_1xj9cTk'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# --- FUNCIÓN DE LIMPIEZA QUIRÚRGICA ---
def limpiar_texto(t):
    # Quita saltos de línea, comillas y espacios sobrantes
    return t.replace('\n', ' ').replace('"', '').strip()

def extraer_url(texto):
    # Busca una URL que empiece con http o https y termina donde hay un espacio o fin de línea
    match = re.search(r'(https?://[^\s]+)', texto)
    return match.group(0) if match else None

def obtener_datos_limpios():
    try:
        r = requests.get(URL_SHEET)
        r.encoding = 'utf-8'
        raw_data = r.text
        
        # Leemos el CSV
        reader = csv.reader(StringIO(raw_data))
        filas_limpias = []
        
        for fila in reader:
            # Limpiamos CADA celda de la fila apenas entra
            nueva_fila = [limpiar_texto(celda) for celda in fila]
            if len(nueva_fila) >= 3:
                filas_limpias.append(nueva_fila)
        return filas_limpias
    except Exception as e:
        print(f"Error lectura: {e}")
        return []

# === COMANDOS ===
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
    bot.reply_to(message, "🚀 *RADAR VIP GLOBAL*\nSeleccioná tu país:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def callback_pais(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = pais
    bot.edit_message_text(f"✅ *{pais}* activado. ¿Qué buscás?", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# === BÚSQUEDA CON INTENCIÓN ===
@bot.message_handler(func=lambda message: True)
def buscar(message):
    chat_id = message.chat.id
    if chat_id not in user_data: return welcome(message)

    pais_user = user_data[chat_id]
    busqueda_usuario = message.text.lower().strip()
    
    bot.send_chat_action(chat_id, 'typing')
    excel_data = obtener_datos_limpios()
    
    encontrados = []

    for fila in excel_data:
        # Fila[0]=Pais, Fila[1]=Nombre/Seccion, Fila[2]=Plataforma, Fila[3]=Link...
        iso = fila[0].upper()
        nombre_item = fila[1].lower()
        plataforma = fila[2].lower()
        
        # Chequeamos si el país coincide
        if iso == pais_user or iso == "GLOBAL":
            # Buscamos la palabra en el Nombre o en la Plataforma
            if busqueda_usuario in nombre_item or busqueda_usuario in plataforma:
                # Buscamos un link real en toda la fila por las dudas
                url_final = None
                for celda in fila:
                    url_final = extraer_url(celda)
                    if url_final: break
                
                if url_final:
                    # Detectar prioridad
                    es_vip = any("1" in c for c in fila[4:]) if len(fila) > 4 else False
                    icono = "🔥" if es_vip else "💎"
                    
                    # Formatear nombre para que no sea gigante
                    nombre_corto = fila[1][:50] + "..." if len(fila[1]) > 53 else fila[1]
                    encontrados.append(f"{icono} *{fila[2]}* - [{nombre_corto}]({url_final})")

    if encontrados:
        res = f"🎯 *Resultados para:* _{busqueda_usuario}_\n\n" + "\n".join(list(set(encontrados))[:10])
    else:
        # Si falla el Excel, Amazon/AliExpress
        q_url = urllib.parse.quote(busqueda_usuario)
        res = f"🎯 No hay secciones exactas para '{busqueda_usuario}'.\nPruebe búsqueda mundial:\n\n"
        res += f"🛒 [Amazon](https://www.amazon.com/s?k={q_url}&tag={AMAZON_TAG})\n"
        res += f"🛍️ [AliExpress](https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url=https://www.aliexpress.com/wholesale?SearchText={q_url})"

    bot.send_message(chat_id, res, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.polling(none_stop=True)
