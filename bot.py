import sqlite3
import requests
import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# 🔐 TOKEN desde variables de entorno (Render)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Falta BOT_TOKEN en variables de entorno")

# 💰 CONFIGURACIÓN AFILIADOS
AMAZON_ID = "radarvip01-20"
SHEET_ID = "1k5ndpAv-r9tOTCgNYDHzpijF0FHPFm7-8DPmMkowSx0" # Tu ID de Google Sheets
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 🌎 MAPA DE MERCADO LIBRE
PAISES_ML = {
    "AR": "MLA",
    "CL": "MLC",
    "MX": "MLM",
    "CO": "MCO",
    "PE": "MPE",
    "BR": "MLB",
    "UY": "MLU",
    "OTRO": "MLM"
}

# 🧠 BASE DE DATOS LOCAL (Para usuarios y créditos)
def db_conn():
    return sqlite3.connect("bot.db")

def init_db():
    conn = db_conn()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, pais TEXT, consultas INT)")
    conn.commit()
    conn.close()

# 📊 FUNCIONES DE USUARIO
def save_user(user_id, pais):
    conn = db_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, COALESCE((SELECT consultas FROM users WHERE id=?), 10))", (user_id, pais, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data

def update_consultas(user_id, n):
    conn = db_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET consultas=? WHERE id=?", (n, user_id))
    conn.commit()
    conn.close()

# 📑 FUNCIÓN PARA LEER EL GOOGLE SHEETS (TU INVENTARIO)
def obtener_productos_vanguardia(pais_usuario):
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.lower()
        
        # Filtramos por país del usuario + lo que es "Global"
        # Si es Chile, filtramos para que NO vea lo marcado como 'propio' en la columna fuente
        if pais_usuario == "CL":
            mask = (df['pais'].str.upper() == "CL") | (df['pais'].str.upper() == "GLOBAL")
            res = df[mask]
            if 'fuente' in res.columns:
                res = res[~res['fuente'].str.contains('propio', case=False, na=False)]
        elif pais_usuario == "AR":
            mask = (df['pais'].str.upper() == "AR") | (df['pais'].str.upper() == "GLOBAL")
            res = df[mask]
        else:
            res = df[df['pais'].str.upper() == "GLOBAL"]
            
        return res.head(5) # Devolvemos los primeros 5 para no saturar el chat
    except Exception as e:
        print(f"Error leyendo Sheets: {e}")
        return pd.DataFrame()

# 🔗 GENERADORES DE LINKS
def link_amazon(q):
    return f"https://www.amazon.com/s?k={q}&tag={AMAZON_ID}"

def link_ali(q):
    return f"https://www.aliexpress.com/wholesale?SearchText={q}"

def buscar_ml_api(site, q):
    try:
        url = f"https://api.mercadolibre.com/sites/{site}/search?q={q}"
        r = requests.get(url).json()
        if r.get("results"):
            item = r["results"][0]
            return f"👉 {item['title']}\n💰 ${item['price']}\n🔗 {item['permalink']}"
    except:
        pass
    return "No encontré resultados en ML en este momento."

# 🚀 COMANDOS TELEGRAM
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [
        [InlineKeyboardButton("🇦🇷 Argentina", callback_data="AR")],
        [InlineKeyboardButton("🇨🇱 Chile", callback_data="CL")],
        [InlineKeyboardButton("🇲🇽 México", callback_data="MX")],
        [InlineKeyboardButton("🇺🇾 Uruguay", callback_data="UY")],
        [InlineKeyboardButton("🌎 Otro", callback_data="OTRO")]
    ]
    await update.message.reply_text(
        "👋 ¡Bienvenido al Bot de Compras Vanguardista!\nSeleccioná tu país para darte las mejores ofertas:",
        reply_markup=InlineKeyboardMarkup(botones)
    )

async def set_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    pais = query.data
    save_user(user_id, pais)
    await query.answer()
    await query.message.reply_text(f"✅ Configurado para {pais}. Escribí qué producto buscás (ej: cuerdas de guitarra).")

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("❌ Por favor, iniciá con /start")
        return

    pais_id = user[1]
    consultas = user[2]

    if consultas <= 0:
        await update.message.reply_text("⛔ Te quedaste sin búsquedas. Escribí /pagar para recargar.")
        return

    query_text = update.message.text
    q_limpio = query_text.replace(" ", "+")

    # Restar una consulta
    update_consultas(user_id, consultas - 1)

    # 1. Buscar en tu Google Sheets (Productos propios/seleccionados)
    mensaje = f"🔎 **Resultados para: {query_text}**\n\n"
    
    mis_prods = obtener_productos_vanguardia(pais_id)
    if not mis_prods.empty:
        mensaje += "🌟 **RECOMENDADOS VANGUARDIA:**\n"
        for _, fila in mis_prods.iterrows():
            mensaje += f"• {fila['nombre']}\n  🔗 {fila['link']}\n\n"

    # 2. Buscar en Mercado Libre General
    site_ml = PAISES_ML.get(pais_id, "MLM")
    mensaje += "🛒 **EN MERCADO LIBRE:**\n"
    mensaje += buscar_ml_api(site_ml, q_limpio) + "\n\n"

    # 3. Links Globales
    mensaje += "🌎 **TIENDAS INTERNACIONALES:**\n"
    mensaje += f"🟡 Amazon: [Ver aquí]({link_amazon(q_limpio)})\n"
    mensaje += f"🔴 AliExpress: [Ver aquí]({link_ali(q_limpio)})\n\n"
    mensaje += f"📉 Te quedan {consultas - 1} búsquedas."

    await update.message.reply_text(mensaje, parse_mode="Markdown", disable_web_page_preview=False)

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 **Suscripción Premium**\n\nRecargá 50 búsquedas por USD 5.\nContacto para pago: @TuUsuarioDeTelegram")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_conn()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 Total de usuarios: {total}")

# ⚙️ INICIO DEL BOT
if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pagar", pagar))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(set_pais))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), buscar))

    print("🚀 BOT DE VANGUARDIA FUNCIONANDO")
    app.run_polling()
