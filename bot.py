import logging, random, os, requests, csv
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"
TOKEN = os.getenv("TELEGRAM_TOKEN")

SELECCION_PAIS, EN_BUSQUEDA = range(2)
logging.basicConfig(level=logging.INFO)

def obtener_datos():
    try:
        r = requests.get(CSV_URL)
        f = StringIO(r.content.decode('utf-8'))
        return list(csv.DictReader(f))
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🇦🇷 AR', '🇨🇱 CL'], ['🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text("✨ **RADAR VIP GLOBAL** ✨\n¿De dónde vienes?", 
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True), parse_mode='Markdown')
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    op = update.message.text.upper()
    if 'AR' in op:
        context.user_data['p'] = 'AR'
        msg = "🇦🇷 **OPORTUNIDADES (AR)**\n\n"
        for r in datos[0:7]: msg += f"🔥 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué andás buscando, che?")
    elif 'CL' in op:
        context.user_data['p'] = 'CL'
        msg = "🇨🇱 **DESTACADOS CHILE**\n\n"
        for r in [datos[i] for i in random.sample(range(96, 184), 3)]: msg += f"✨ {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscái hoy, po?")
    elif 'UY' in op:
        context.user_data['p'] = 'UY'
        msg = "🇺🇾 **SUGERENCIAS URUGUAY**\n\n"
        for r in [datos[184], datos[185], datos[186]]: msg += f"🇺🇾 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscás, bo?")
    else:
        context.user_data['p'] = 'GL'
        msg = "🌎 **GLOBAL DEALS**\n\n"
        for r in datos[185:187]: msg += f"📦 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("What are you looking for?")
    return EN_BUSQUEDA

async def ejecutar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    q = update.message.text.lower()
    p = context.user_data.get('p')
    idx = (list(range(0, 96)) + [185, 186]) if p == 'AR' else (list(range(96, 184)) + [185, 186]) if p == 'CL' else [184, 185, 186] if p == 'UY' else [185, 186]
    res = [datos[i] for i in idx if i < len(datos) and (q in str(datos[i].get('Keywords','')).lower() or q in str(datos[i].get('Producto','')).lower())]
    if res:
        for x in res[:5]: await update.message.reply_text(f"📍 **{x['Producto']}**\n🔗 {x['Link']}", parse_mode='Markdown')
    else:
        await update.message.reply_text("Nada local, mira esto global:")
        for i in [185, 186]: await update.message.reply_text(f"🌎 {datos[i]['Producto']}\n🔗 {datos[i]['Link']}")
    return EN_BUSQUEDA

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(ConversationHandler(entry_points=[CommandHandler('start', start)], 
        states={SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)], 
        EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ejecutar_busqueda)]}, 
        fallbacks=[CommandHandler('start', start)]))
    app.run_polling()
