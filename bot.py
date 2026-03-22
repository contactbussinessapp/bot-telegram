import os
import telebot
import pandas as pd
import requests

# CONFIGURACIÓN CRÍTICA
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
SHEET_NAME = 'Sheet1'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

bot = telebot.TeleBot(TOKEN)
user_data = {}

def buscar_en_excel(query, pais_usuario):
    try:
        df = pd.read_csv(URL_SHEET)
        # Limpieza de nombres de columnas por si acaso
        df.columns = df.columns.str.strip().str.lower()
        
        # FILTRO INTELIGENTE: Busca la palabra dentro del título largo (sin importar mayúsculas)
        query = str(query).lower()
        resultado = df[
            (df['nombre'].astype(str).str.lower().str.contains(query)) & 
            (df['pais'].astype(str).str.upper() == pais_usuario.upper())
        ]
        return resultado
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return pd.DataFrame()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🇦🇷 Argentina", callback_data="set_AR"))
    markup.add(telebot.types.InlineKeyboardButton("🇺🇾 Uruguay", callback_data="set_UY"))
    bot.reply_to(message, "✨ **Radar VIP Global** ✨\nSeleccioná tu país para activar las ofertas:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais = call.data.split("_")[1]
    user_data[call.message.chat.id] = {'pais': pais, 'busquedas': 10}
    bot.answer_callback_query(call.id, f"Configurado para {pais}")
    bot.edit_message_text(f"✅ **Configurado para {pais}**. Escribí qué buscás (ej: caña o peugeot).", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "Primero poné /start para elegir tu país.")
        return

    query = message.text
    pais = user_data[chat_id]['pais']
    
    # 1. BUSCAR PRIMERO EN TU EXCEL (TU STOCK)
    mis_productos = buscar_en_excel(query, pais)
    
    respuesta = f"🔍 **Resultados para: {query}**\n\n"
    
    if not mis_productos.empty:
        respuesta += "🌟 **RECOMENDADOS VANGUARDIA (Tu Stock)** 🌟\n"
        for _, row in mis_productos.iterrows():
            respuesta += f"✅ [{row['nombre']}]({row['link']}) — *{row['fuente']}*\n"
        respuesta += "\n---\n"

    # 2. AGREGAR LINKS GENERALES
    respuesta += "📦 **TIENDAS INTERNACIONALES:**\n"
    respuesta += f"🔹 [Amazon](https://www.amazon.com/s?k={query.replace(' ', '+')})\n"
    respuesta += f"🔹 [AliExpress](https://www.aliexpress.com/wholesale?SearchText={query.replace(' ', '+')})\n"
    
    user_data[chat_id]['busquedas'] -= 1
    respuesta += f"\n📉 *Te quedan {user_data[chat_id]['busquedas']} búsquedas.*"
    
    bot.send_message(chat_id, respuesta, parse_mode="Markdown", disable_web_page_preview=False)

bot.polling()
