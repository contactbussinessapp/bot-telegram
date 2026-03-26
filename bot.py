import logging
import random
import os
import requests
import csv
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURACIÓN ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Estados de la conversación
SELECCION_PAIS, EN_BUSQUEDA = range(2)

logging.basicConfig(level=logging.INFO)

def obtener_datos():
    try:
        response = requests.get(CSV_URL)
        f = StringIO(response.content.decode('utf-8'))
        reader = csv.DictReader(f)
        return list(reader)
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Paso 1: Pregunta origen con Banderas"""
    botones = [['🇦🇷 AR', '🇨🇱 CL'], ['🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text(
        "✨ **RADAR VIP GLOBAL** ✨\n\n¿Desde dónde nos visitas hoy?",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True, one_time_keyboard=True)
    )
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    if not datos:
        await update.message.reply_text("Error de conexión con la base de datos.")
        return ConversationHandler.END

    opcion = update.message.text
    
    # --- 2. LÓGICA ARGENTINA (Filas 2 a 8 = index 0 a 6) ---
    if 'AR' in opcion:
        context.user_data['pais'] = 'AR'
        # 2.1 Oportunidades del día (F2 a F8)
        oportunidades = datos[0:7]
        msg = "🇦🇷 **OPORTUNIDADES DEL DÍA (AR)** 🇦🇷\n\n"
        for r in oportunidades:
            msg += f"🔥 {r.get('Producto')}\n🔗 {r.get('Link')}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué andás buscando, che? Decime y te lo encuentro.")

    # --- 3. LÓGICA CHILE (Filas 98 a 185 = index 96 a 183) ---
    elif 'CL' in opcion:
        context.user_data['pais'] = 'CL'
        # 3.1 Productos al azar (F98-185 + F187-188)
        rango_cl = list(range(96, 184)) + [185, 186]
        azar = [datos[i] for i in random.sample(rango_cl, 3)]
        msg = "🇨🇱 **DESTACADOS CHILE** 🇨🇱\n\n"
        for r in azar:
            msg += f"✨ {r.get('Producto')}\n🔗 {r.get('Link')}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscái hoy? Dime qué necesitái y te ayudo al tiro.")

    # --- 4. LÓGICA URUGUAY (Fila 186 = index 184) ---
    elif 'UY' in opcion:
        context.user_data['pais'] = 'UY'
        # 4.1 Productos al azar (F186 + F187-188)
        rango_uy = [184, 185, 186]
        azar = [datos[i] for i in random.sample(rango_uy, 2)]
        msg = "🇺🇾 **SUGERENCIAS URUGUAY** 🇺🇾\n\n"
        for r in azar:
            msg += f"🇺🇾 {r.get('Producto')}\n🔗 {r.get('Link')}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscás, bo? Decime y bicho qué hay.")

    # --- 5. LÓGICA GLOBAL (Filas 187 a 188 = index 185 a 186) ---
    else:
        context.user_data['pais'] = 'GLOBAL'
        # 5.1 Productos al azar (F187-188)
        rango_gl = [185, 186]
        azar = [datos[i] for i in rango_gl]
        msg = "🌎 **GLOBAL DEALS** 🌎\n\n"
        for r in azar:
            msg += f"📦 {r.get('Producto')}\n🔗 {r.get('Link')}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("What are you looking for? / ¿Qué buscas? / O que você está procurando?")

    return EN_BUSQUEDA

async def ejecutar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    query = update.message.text.lower()
    pais = context.user_data.get('pais')

    # Definir rangos exactos de búsqueda por instrucción
    if pais == 'AR':
        indices = list(range(0, 96)) + [185, 186] # F2-97 y F187-188
    elif pais == 'CL':
        indices = list(range(96, 184)) + [185, 186] # F98-185 y F187-188
    elif pais == 'UY':
        indices = [184, 185, 186] # F186 y F187-188
    else:
        indices = [185, 186] # F187-188

    # Buscar coincidencia y relacionados
    encontrados = []
    for i in indices:
        if i < len(datos):
            row = datos[i]
            if query in str(row.get('Keywords', '')).lower() or query in str(row.get('Producto', '')).lower():
                encontrados.append(row)

    if encontrados:
        await update.message.reply_text("✅ ¡Mira lo que encontré!")
        # Muestra hasta 5 resultados (el buscado + relacionados)
        for res in encontrados[:5]:
            await update.message.reply_text(f"📍 **{res.get('Producto')}**\n🔗 {res.get('Link')}", parse_mode='Markdown')
    else:
        # Si no hay éxito local, ofrece Globales
        await update.message.reply_text("No encontré eso localmente, pero chequea estas opciones globales:")
        for idx in [185, 186]:
            row = datos[idx]
            await update.message.reply_text(f"🌎 {row.get('Producto')}\n🔗 {row.get('Link')}")

    return EN_BUSQUEDA

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)],
            EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ejecutar_busqueda)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    application.add_handler(conv_handler)
    application.run_polling()
