import logging
import random
import os
import pandas as pd
import requests
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURACIÓN SEGURA ---
# El link del CSV es público por diseño, pero el TOKEN NO.
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"

# Render leerá el token desde sus variables de entorno
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Estados de la conversación
SELECCION_PAIS, EN_BUSQUEDA = range(2)

logging.basicConfig(level=logging.INFO)

def obtener_datos():
    """Descarga los datos actualizados del Google Sheet"""
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()
        decode_data = StringIO(response.content.decode('utf-8'))
        df = pd.read_csv(decode_data)
        df.columns = ['Pais', 'Plataforma', 'Producto', 'Keywords', 'Link', 'Prioridad']
        return df
    except Exception as e:
        logging.error(f"Error al obtener datos: {e}")
        return None

# --- LÓGICA DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🇦🇷 AR', '🇨🇱 CL', '🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text(
        "✨ BIENVENIDO A RADAR VIP GLOBAL ✨\n¿Desde dónde nos visitas hoy?",
        reply_markup=ReplyKeyboardMarkup(botones, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = obtener_datos()
    if df is None:
        await update.message.reply_text("Error de conexión. Intenta más tarde.")
        return ConversationHandler.END

    seleccion = update.message.text
    context.user_data['pais'] = seleccion

    if 'AR' in seleccion:
        oportunidades = df.iloc[0:7] 
        msg = "🇦🇷 **OPORTUNIDADES DEL DÍA (AR)** 🇦🇷\n\n"
        for _, row in oportunidades.iterrows():
            msg += f"🔥 {row['Producto']}\n🔗 {row['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué andás buscando, che? Decime.")

    elif 'CL' in seleccion:
        rango_cl = list(range(96, 184))
        azar = df.iloc[random.sample(rango_cl, 3)]
        msg = "🇨🇱 **DESTACADOS CHILE** 🇨🇱\n\n"
        for _, row in azar.iterrows():
            msg += f"✨ {row['Producto']}\n🔗 {row['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscái hoy? Dime qué necesitái.")

    elif 'UY' in seleccion:
        indices_uy = [184, 185, 186]
        azar = df.iloc[random.sample(indices_uy, 2)]
        msg = "🇺🇾 **SUGERENCIAS URUGUAY** 🇺🇾\n\n"
        for _, row in azar.iterrows():
            msg += f"🇺🇾 {row['Producto']}\n🔗 {row['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscás, bo? Decime.")

    else:
        globales = df.iloc[185:187]
        msg = "🌎 **GLOBAL DEALS** 🌎\n\n"
        for _, row in globales.iterrows():
            msg += f"📦 {row['Producto']}\n🔗 {row['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("What are you looking for? / ¿Qué buscas?")

    return EN_BUSQUEDA

async def ejecutar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = obtener_datos()
    query = update.message.text.lower()
    pais = context.user_data.get('pais')

    if 'AR' in pais:
        rango = list(range(0, 96)) + [185, 186]
    elif 'CL' in pais:
        rango = list(range(96, 184)) + [185, 186]
    elif 'UY' in pais:
        rango = [184, 185, 186]
    else:
        rango = [185, 186]

    subset = df.iloc[rango]
    encontrados = []

    for _, row in subset.iterrows():
        if query in str(row['Keywords']).lower():
            encontrados.append(row)

    if encontrados:
        await update.message.reply_text("✅ ¡Encontré esto!")
        for res in encontrados[:4]:
            await update.message.reply_text(f"📍 **{res['Producto']}**\n🔗 {res['Link']}", parse_mode='Markdown')
    else:
        await update.message.reply_text("Sin éxito local, bichea en Global:")
        for idx in [185, 186]:
            row = df.iloc[idx]
            await update.message.reply_text(f"🌎 {row['Producto']}\n🔗 {row['Link']}")

    return EN_BUSQUEDA

if __name__ == '__main__':
    if not TOKEN:
        print("ERROR: No se encontró el TOKEN en las variables de entorno.")
    else:
        application = Application.builder().token(TOKEN).build()
        handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)],
                EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ejecutar_busqueda)],
            },
            fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
        )
        application.add_handler(handler)
        application.run_polling()
