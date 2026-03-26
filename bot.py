import logging, random, os, requests, csv
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURACIÓN ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSU00GJR_bjeMwu_2SdaU_Lrym18DZYQKYA0-uW7mzw_2KMbcNYfCAD34mLjHZpKRZH3oOviud0agl3/pub?gid=0&single=true&output=csv"
TOKEN = os.getenv("TELEGRAM_TOKEN")

SELECCION_PAIS, EN_BUSQUEDA = range(2)
logging.basicConfig(level=logging.INFO)

def obtener_datos():
    try:
        r = requests.get(CSV_URL, timeout=10)
        f = StringIO(r.content.decode('utf-8'))
        return list(csv.DictReader(f))
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # PUNTO 1: MOSTRAR BANDERAS
    botones = [['🇦🇷 AR', '🇨🇱 CL'], ['🇺🇾 UY', '🌎 GLOBAL']]
    await update.message.reply_text(
        "✨ **RADAR VIP GLOBAL** ✨\n¿Desde dónde nos visitas hoy?", 
        reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True, one_time_keyboard=True),
        parse_mode='Markdown'
    )
    return SELECCION_PAIS

async def seleccionar_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    if not datos:
        await update.message.reply_text("Error de base de datos.")
        return ConversationHandler.END
        
    op = update.message.text.upper()
    
    if 'AR' in op:
        context.user_data['p'] = 'AR'
        # 2.1: Filas 2 a 8 (idx 0 a 6)
        msg = "🇦🇷 **OPORTUNIDADES DEL DÍA (AR)** 🇦🇷\n\n"
        for r in datos[0:7]: msg += f"🔥 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué andás buscando, che? Decime y te lo encuentro.")
    
    elif 'CL' in op:
        context.user_data['p'] = 'CL'
        # 3.1: Azar F98-185 (idx 96-183) + Global (idx 185-186)
        rango = list(range(96, 184)) + [185, 186]
        azar = [datos[i] for i in random.sample(rango, 3)]
        msg = "🇨🇱 **DESTACADOS CHILE** 🇨🇱\n\n"
        for r in azar: msg += f"✨ {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscái hoy? Dime qué necesitái y te ayudo al tiro.")
    
    elif 'UY' in op:
        context.user_data['p'] = 'UY'
        # 4.1: F186 (idx 184) + Global (idx 185-186)
        rango = [184, 185, 186]
        azar = [datos[i] for i in random.sample(rango, 2)]
        msg = "🇺🇾 **SUGERENCIAS URUGUAY** 🇺🇾\n\n"
        for r in azar: msg += f"🇺🇾 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("¿Qué buscás, bo? Decime y bicho qué hay.")
    
    else:
        context.user_data['p'] = 'GL'
        # 5.1: Global (idx 185-186)
        msg = "🌎 **GLOBAL DEALS** 🌎\n\n"
        for i in [185, 186]:
            r = datos[i]
            msg += f"📦 {r['Producto']}\n🔗 {r['Link']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        await update.message.reply_text("What are you looking for? / ¿Qué buscas?")
        
    return EN_BUSQUEDA

async def ejecutar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_datos()
    query = update.message.text.lower()
    p = context.user_data.get('p')
    
    if p == 'AR': idxs = list(range(0, 96)) + [185, 186]
    elif p == 'CL': idxs = list(range(96, 184)) + [185, 186]
    elif p == 'UY': idxs = [184, 185, 186]
    else: idxs = [185, 186]
    
    encontrados = [datos[i] for i in idxs if i < len(datos) and (query in str(datos[i].get('Keywords','')).lower() or query in str(datos[i].get('Producto','')).lower())]
    
    if encontrados:
        await update.message.reply_text("✅ ¡Mira lo que encontré!")
        for x in encontrados[:5]: await update.message.reply_text(f"📍 **{x['Producto']}**\n🔗 {x['Link']}", parse_mode='Markdown')
    else:
        await update.message.reply_text("No hay éxito local, bichea Global:")
        for i in [185, 186]: await update.message.reply_text(f"🌎 {datos[i]['Producto']}\n🔗 {datos[i]['Link']}")
    return EN_BUSQUEDA

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECCION_PAIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_pais)],
            EN_BUSQUEDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ejecutar_busqueda)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    application.add_handler(conv)
    print("Radar VIP Online...")
    application.run_polling(drop_pending_updates=True)
