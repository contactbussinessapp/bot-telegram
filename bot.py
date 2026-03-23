import os
import telebot
import requests
import csv
import random
import urllib.parse
import re
from io import StringIO

# === 1. CONFIGURACIÓN DE CREDENCIALES ===
TOKEN = os.environ.get('TOKEN')
SHEET_ID = '1_NFTMtOtxiIB4vg6h01VL5dAdDnTT7x5jbFjIvPUnTY'
URL_SHEET = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

AMAZON_TAG = "radarvip01-20"
ALI_KEY = "_c3MIbod9"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# === 2. DICCIONARIO DE IDIOMAS (TEXTS) ===
TEXTS = {
    'es': {
        'configured': "✅ *Configurado para {name} {flag}*\n\n¿Qué producto estás buscando hoy? Escríbelo aquí abajo:",
        'searching': "🔍 *Rastreando bóvedas...*", 'results_for': "🎯 *Resultados para:* _{query}_\n\n",
        'vip_local': "🔥 *Oportunidades VIP Locales:*\n", 'stores': "🌐 *Buscar en tiendas (Mejores precios):*\n",
        'ml': "🤝 [Ver opciones en Mercado Libre]", 'amz': "🛒 [Ver opciones en Amazon]", 'ali': "🛍️ [Ver opciones en AliExpress]",
        'error_text': "⚠️ Por favor, escribe el nombre usando letras.", 'error_conn': "⚠️ Error de conexión. Intenta nuevamente."
    },
    'en': {
        'configured': "✅ *Set to {name} {flag}*\n\nWhat product are you looking for today? Type it below:",
        'searching': "🔍 *Scanning vaults...*", 'results_for': "🎯 *Results for:* _{query}_\n\n",
        'vip_local': "🔥 *Local VIP Deals:*\n", 'stores': "🌐 *Search in stores (Best prices):*\n",
        'ml': "🤝 [View on Mercado Libre]", 'amz': "🛒 [View on Amazon]", 'ali': "🛍️ [View on AliExpress]",
        'error_text': "⚠️ Please enter the product name using letters.", 'error_conn': "⚠️ Connection error. Please try again."
    },
    'pt': {
        'configured': "✅ *Configurado para {name} {flag}*\n\nQual produto você está procurando hoje? Digite abaixo:",
        'searching': "🔍 *Rastreando cofres...*", 'results_for': "🎯 *Resultados para:* _{query}_\n\n",
        'vip_local': "🔥 *Ofertas VIP Locais:*\n", 'stores': "🌐 *Buscar nas lojas (Melhores preços):*\n",
        'ml': "🤝 [Ver opções no Mercado Livre]", 'amz': "🛒 [Ver opções na Amazon]", 'ali': "🛍️ [Ver opções no AliExpress]",
        'error_text': "⚠️ Por favor, digite o nome usando letras.", 'error_conn': "⚠️ Erro de conexão. Tente novamente."
    },
    'hi': {
        'configured': "✅ *{name} {flag} के लिए सेट किया गया*\n\nआज आप कौन सा उत्पाद ढूंढ रहे हैं? इसे नीचे लिखें:",
        'searching': "🔍 *वॉल्ट स्कैन कर रहे हैं...*", 'results_for': "🎯 *परिणाम:* _{query}_\n\n",
        'vip_local': "🔥 *स्थानीय VIP सौदे:*\n", 'stores': "🌐 *स्टोर में खोजें (सर्वोत्तम मूल्य):*\n",
        'ml': "🤝 [Mercado Libre पर देखें]", 'amz': "🛒 [Amazon पर देखें]", 'ali': "🛍️ [AliExpress पर देखें]",
        'error_text': "⚠️ कृपया अक्षरों का उपयोग करके नाम दर्ज करें।", 'error_conn': "⚠️ कनेक्शन त्रुटि। कृपया पुनः प्रयास करें।"
    },
    'de': {
        'configured': "✅ *Eingestellt auf {name} {flag}*\n\nWelches Produkt suchen Sie heute? Geben Sie es unten ein:",
        'searching': "🔍 *Tresore werden durchsucht...*", 'results_for': "🎯 *Ergebnisse für:* _{query}_\n\n",
        'vip_local': "🔥 *Lokale VIP-Angebote:*\n", 'stores': "🌐 *In Geschäften suchen (Beste Preise):*\n",
        'ml': "🤝 [Auf Mercado Libre ansehen]", 'amz': "🛒 [Auf Amazon ansehen]", 'ali': "🛍️ [Auf AliExpress ansehen]",
        'error_text': "⚠️ Bitte geben Sie den Namen in Buchstaben ein.", 'error_conn': "⚠️ Verbindungsfehler. Bitte erneut versuchen."
    },
    'fr': {
        'configured': "✅ *Configuré pour {name} {flag}*\n\nQuel produit recherchez-vous aujourd'hui ? Écrivez-le ci-dessous :",
        'searching': "🔍 *Recherche dans les coffres...*", 'results_for': "🎯 *Résultats pour :* _{query}_\n\n",
        'vip_local': "🔥 *Offres VIP locales :*\n", 'stores': "🌐 *Rechercher dans les magasins (Meilleurs prix) :*\n",
        'ml': "🤝 [Voir sur Mercado Libre]", 'amz': "🛒 [Voir sur Amazon]", 'ali': "🛍️ [Voir sur AliExpress]",
        'error_text': "⚠️ Veuillez entrer le nom avec des lettres.", 'error_conn': "⚠️ Erreur de connexion. Veuillez réessayer."
    },
    'it': {
        'configured': "✅ *Impostato su {name} {flag}*\n\nChe prodotto stai cercando oggi? Scrivilo qui sotto:",
        'searching': "🔍 *Scansione dei caveau...*", 'results_for': "🎯 *Risultati per:* _{query}_\n\n",
        'vip_local': "🔥 *Offerte VIP locali:*\n", 'stores': "🌐 *Cerca nei negozi (Migliori prezzi):*\n",
        'ml': "🤝 [Vedi su Mercado Libre]", 'amz': "🛒 [Vedi su Amazon]", 'ali': "🛍️ [Vedi su AliExpress]",
        'error_text': "⚠️ Inserisci il nome usando lettere.", 'error_conn': "⚠️ Errore di connessione. Riprova."
    },
    'ja': {
        'configured': "✅ *{name} {flag} に設定されました*\n\n今日はどの商品をお探しですか？ 下に入力してください：",
        'searching': "🔍 *保管庫をスキャン中...*", 'results_for': "🎯 *検索結果:* _{query}_\n\n",
        'vip_local': "🔥 *ローカルVIP特典:*\n", 'stores': "🌐 *ストアで検索 (最安値):*\n",
        'ml': "🤝 [Mercado Libreで見る]", 'amz': "🛒 [Amazonで見る]", 'ali': "🛍️ [AliExpressで見る]",
        'error_text': "⚠️ 商品名は文字で入力してください。", 'error_conn': "⚠️ 接続エラー。もう一度お試しください。"
    },
    'ko': {
        'configured': "✅ *{name} {flag} (으)로 설정됨*\n\n오늘 어떤 상품을 찾고 계신가요? 아래에 입력하세요:",
        'searching': "🔍 *금고 스캔 중...*", 'results_for': "🎯 *검색 결과:* _{query}_\n\n",
        'vip_local': "🔥 *로컬 VIP 특가:*\n", 'stores': "🌐 *스토어 검색 (최저가):*\n",
        'ml': "🤝 [Mercado Libre에서 보기]", 'amz': "🛒 [Amazon에서 보기]", 'ali': "🛍️ [AliExpress에서 보기]",
        'error_text': "⚠️ 상품명은 문자로 입력해주세요.", 'error_conn': "⚠️ 연결 오류. 다시 시도해주세요."
    },
    'ar': {
        'configured': "✅ *تم الإعداد لـ {name} {flag}*\n\nما المنتج الذي تبحث عنه اليوم؟ اكتبه بالأسفل:",
        'searching': "🔍 *جارٍ البحث في الخزائن...*", 'results_for': "🎯 *نتائج لـ:* _{query}_\n\n",
        'vip_local': "🔥 *عروض VIP المحلية:*\n", 'stores': "🌐 *البحث في المتاجر (أفضل الأسعار):*\n",
        'ml': "🤝 [عرض على Mercado Libre]", 'amz': "🛒 [عرض على Amazon]", 'ali': "🛍️ [عرض على AliExpress]",
        'error_text': "⚠️ الرجاء إدخال الاسم باستخدام الحروف.", 'error_conn': "⚠️ خطأ في الاتصال. حاول مرة أخرى."
    },
    'ru': {
        'configured': "✅ *Настроено для {name} {flag}*\n\nКакой товар вы ищете сегодня? Напишите ниже:",
        'searching': "🔍 *Сканирование хранилищ...*", 'results_for': "🎯 *Результаты для:* _{query}_\n\n",
        'vip_local': "🔥 *Местные VIP-предложения:*\n", 'stores': "🌐 *Поиск в магазинах (Лучшие цены):*\n",
        'ml': "🤝 [Смотреть на Mercado Libre]", 'amz': "🛒 [Смотреть на Amazon]", 'ali': "🛍️ [Смотреть на AliExpress]",
        'error_text': "⚠️ Пожалуйста, введите название буквами.", 'error_conn': "⚠️ Ошибка подключения. Попробуйте еще раз."
    },
    'af': {
        'configured': "✅ *Opgestel vir {name} {flag}*\n\nWatter produk soek jy vandag? Tik dit hieronder:",
        'searching': "🔍 *Skandeer kluise...*", 'results_for': "🎯 *Resultate vir:* _{query}_\n\n",
        'vip_local': "🔥 *Plaaslike VIP-aanbiedings:*\n", 'stores': "🌐 *Soek in winkels (Beste pryse):*\n",
        'ml': "🤝 [Kyk op Mercado Libre]", 'amz': "🛒 [Kyk op Amazon]", 'ali': "🛍️ [Kyk op AliExpress]",
        'error_text': "⚠️ Voer asseblief die naam in met letters.", 'error_conn': "⚠️ Verbindingsfout. Probeer asseblief weer."
    },
    'tr': {
        'configured': "✅ *{name} {flag} olarak ayarlandı*\n\nBugün hangi ürünü arıyorsunuz? Aşağıya yazın:",
        'searching': "🔍 *Kasalar taranıyor...*", 'results_for': "🎯 *Sonuçlar:* _{query}_\n\n",
        'vip_local': "🔥 *Yerel VIP Fırsatları:*\n", 'stores': "🌐 *Mağazalarda ara (En iyi fiyatlar):*\n",
        'ml': "🤝 [Mercado Libre'de Gör]", 'amz': "🛒 [Amazon'da Gör]", 'ali': "🛍️ [AliExpress'te Gör]",
        'error_text': "⚠️ Lütfen harfleri kullanarak bir isim girin.", 'error_conn': "⚠️ Bağlantı hatası. Lütfen tekrar deneyin."
    },
    'sv': {
        'configured': "✅ *Inställd på {name} {flag}*\n\nVilken produkt letar du efter idag? Skriv nedan:",
        'searching': "🔍 *Skannar valv...*", 'results_for': "🎯 *Resultat för:* _{query}_\n\n",
        'vip_local': "🔥 *Lokala VIP-erbjudanden:*\n", 'stores': "🌐 *Sök i butiker (Bästa priserna):*\n",
        'ml': "🤝 [Visa på Mercado Libre]", 'amz': "🛒 [Visa på Amazon]", 'ali': "🛍️ [Visa på AliExpress]",
        'error_text': "⚠️ Vänligen ange namnet med bokstäver.", 'error_conn': "⚠️ Anslutningsfel. Försök igen."
    },
    'no': {
        'configured': "✅ *Satt til {name} {flag}*\n\nHvilket produkt leter du etter i dag? Skriv nedenfor:",
        'searching': "🔍 *Skanner hvelv...*", 'results_for': "🎯 *Resultater for:* _{query}_\n\n",
        'vip_local': "🔥 *Lokale VIP-tilbud:*\n", 'stores': "🌐 *Søk i butikker (Beste priser):*\n",
        'ml': "🤝 [Vis på Mercado Libre]", 'amz': "🛒 [Vis på Amazon]", 'ali': "🛍️ [Vis på AliExpress]",
        'error_text': "⚠️ Vennligst skriv inn navnet med bokstaver.", 'error_conn': "⚠️ Tilkoblingsfeil. Prøv igjen."
    },
    'fi': {
        'configured': "✅ *Asetettu: {name} {flag}*\n\nMitä tuotetta etsit tänään? Kirjoita alle:",
        'searching': "🔍 *Skannataan holveja...*", 'results_for': "🎯 *Tulokset:* _{query}_\n\n",
        'vip_local': "🔥 *Paikalliset VIP-tarjoukset:*\n", 'stores': "🌐 *Etsi kaupoista (Parhaat hinnat):*\n",
        'ml': "🤝 [Katso Mercado Libre]", 'amz': "🛒 [Katso Amazon]", 'ali': "🛍️ [Katso AliExpress]",
        'error_text': "⚠️ Kirjoita nimi kirjaimilla.", 'error_conn': "⚠️ Yhteysvirhe. Yritä uudelleen."
    }
}

# === 3. DICCIONARIO MAESTRO DE PAÍSES ===
COUNTRY_CONFIG = {
    # --- AMÉRICA ---
    'AR': {'name': 'Argentina', 'flag': '🇦🇷', 'lang': 'es', 'show_ml': True, 'ml_domain': 'com.ar', 'ml_tool': '85456160', 'ml_camp': 'RadarVIPBot', 'show_amz': False, 'show_ali': True, 'show_vip': True},
    'CL': {'name': 'Chile', 'flag': '🇨🇱', 'lang': 'es', 'show_ml': True, 'ml_domain': 'cl', 'ml_tool': '65347472', 'ml_camp': 'RadarVIPChile', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'UY': {'name': 'Uruguay', 'flag': '🇺🇾', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'PY': {'name': 'Paraguay', 'flag': '🇵🇾', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'CO': {'name': 'Colombia', 'flag': '🇨🇴', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'PE': {'name': 'Perú', 'flag': '🇵🇪', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'EC': {'name': 'Ecuador', 'flag': '🇪🇨', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'MX': {'name': 'México', 'flag': '🇲🇽', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'BR': {'name': 'Brasil', 'flag': '🇧🇷', 'lang': 'pt', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'US': {'name': 'USA', 'flag': '🇺🇸', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': True, 'show_ali': True, 'show_vip': False},
    'CA': {'name': 'Canada', 'flag': '🇨🇦', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    
    # --- EUROPA ---
    'ES': {'name': 'España', 'flag': '🇪🇸', 'lang': 'es', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'UK': {'name': 'UK', 'flag': '🇬🇧', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'DE': {'name': 'Deutschland', 'flag': '🇩🇪', 'lang': 'de', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'FR': {'name': 'France', 'flag': '🇫🇷', 'lang': 'fr', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'IT': {'name': 'Italia', 'flag': '🇮🇹', 'lang': 'it', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'RU': {'name': 'Россия', 'flag': '🇷🇺', 'lang': 'ru', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'SE': {'name': 'Sverige', 'flag': '🇸🇪', 'lang': 'sv', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'NO': {'name': 'Norge', 'flag': '🇳🇴', 'lang': 'no', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'FI': {'name': 'Suomi', 'flag': '🇫🇮', 'lang': 'fi', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    
    # --- ASIA Y OCEANÍA ---
    'IN': {'name': 'India', 'flag': '🇮🇳', 'lang': 'hi', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'JP': {'name': '日本', 'flag': '🇯🇵', 'lang': 'ja', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'KR': {'name': '대한민국', 'flag': '🇰🇷', 'lang': 'ko', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'TR': {'name': 'Türkiye', 'flag': '🇹🇷', 'lang': 'tr', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'AU': {'name': 'Australia', 'flag': '🇦🇺', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    
    # --- ÁFRICA ---
    'ZA': {'name': 'South Africa', 'flag': '🇿🇦', 'lang': 'af', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'NG': {'name': 'Nigeria', 'flag': '🇳🇬', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},
    'EG': {'name': 'مصر', 'flag': '🇪🇬', 'lang': 'ar', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False},

    'GLOBAL': {'name': 'Global', 'flag': '🌍', 'lang': 'en', 'show_ml': False, 'ml_domain': '', 'show_amz': False, 'show_ali': True, 'show_vip': False}
}

# === 4. BIENVENIDA Y MENÚ DESPLEGADO ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    
    botones = [
        telebot.types.InlineKeyboardButton("🇦🇷 AR", callback_data="set_AR"),
        telebot.types.InlineKeyboardButton("🇨🇱 CL", callback_data="set_CL"),
        telebot.types.InlineKeyboardButton("🇺🇾 UY", callback_data="set_UY"),
        telebot.types.InlineKeyboardButton("🇵🇾 PY", callback_data="set_PY"),
        telebot.types.InlineKeyboardButton("🇨🇴 CO", callback_data="set_CO"),
        telebot.types.InlineKeyboardButton("🇵🇪 PE", callback_data="set_PE"),
        telebot.types.InlineKeyboardButton("🇪🇨 EC", callback_data="set_EC"),
        telebot.types.InlineKeyboardButton("🇲🇽 MX", callback_data="set_MX"),
        telebot.types.InlineKeyboardButton("🇧🇷 BR", callback_data="set_BR"),
        telebot.types.InlineKeyboardButton("🇺🇸 US", callback_data="set_US"),
        telebot.types.InlineKeyboardButton("🇨🇦 CA", callback_data="set_CA"),
        telebot.types.InlineKeyboardButton("🇪🇸 ES", callback_data="set_ES"),
        telebot.types.InlineKeyboardButton("🇬🇧 UK", callback_data="set_UK"),
        telebot.types.InlineKeyboardButton("🇩🇪 DE", callback_data="set_DE"),
        telebot.types.InlineKeyboardButton("🇫🇷 FR", callback_data="set_FR"),
        telebot.types.InlineKeyboardButton("🇮🇹 IT", callback_data="set_IT"),
        telebot.types.InlineKeyboardButton("🇷🇺 RU", callback_data="set_RU"),
        telebot.types.InlineKeyboardButton("🇸🇪 SE", callback_data="set_SE"),
        telebot.types.InlineKeyboardButton("🇳🇴 NO", callback_data="set_NO"),
        telebot.types.InlineKeyboardButton("🇫🇮 FI", callback_data="set_FI"),
        telebot.types.InlineKeyboardButton("🇮🇳 IN", callback_data="set_IN"),
        telebot.types.InlineKeyboardButton("🇯🇵 JP", callback_data="set_JP"),
        telebot.types.InlineKeyboardButton("🇰🇷 KR", callback_data="set_KR"),
        telebot.types.InlineKeyboardButton("🇹🇷 TR", callback_data="set_TR"),
        telebot.types.InlineKeyboardButton("🇦🇺 AU", callback_data="set_AU"),
        telebot.types.InlineKeyboardButton("🇿🇦 ZA", callback_data="set_ZA"),
        telebot.types.InlineKeyboardButton("🇳🇬 NG", callback_data="set_NG"),
        telebot.types.InlineKeyboardButton("🇪🇬 EG", callback_data="set_EG")
    ]
    
    for i in range(0, len(botones), 4):
        markup.row(*botones[i:i+4])
    
    markup.row(telebot.types.InlineKeyboardButton("🌍 GLOBAL", callback_data="set_GLOBAL"))
    
    bot.reply_to(message, "LANGUAGE", reply_markup=markup, parse_mode="Markdown")

# === 5. ASIGNACIÓN DEL PAÍS ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def set_country(call):
    pais_code = call.data.split("_")[1]
    
    if pais_code in COUNTRY_CONFIG:
        user_data[call.message.chat.id] = {'pais': pais_code}
        config = COUNTRY_CONFIG[pais_code]
        idioma = config['lang']
        t = TEXTS[idioma]
        
        mensaje_ok = t['configured'].format(name=config['name'], flag=config['flag'])
        bot.edit_message_text(mensaje_ok, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# === 6. MOTOR DE BÚSQUEDA Y MONETIZACIÓN ===
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    chat_id = message.chat.id

    if chat_id not in user_data:
        bot.reply_to(message, "⚠️ LANGUAGE", reply_markup=None) 
        return

    pais_code = user_data[chat_id]['pais']
    config = COUNTRY_CONFIG[pais_code]
    idioma = config['lang']
    t = TEXTS[idioma]

    texto_original = message.text.lower()
    query_limpia = re.sub(r'[^\w\s]', '', texto_original).strip()

    if not query_limpia:
        bot.reply_to(message, t['error_text'])
        return

    query_url_amz = query_limpia.replace(' ', '+')
    query_url_ml = query_limpia.replace(' ', '-')

    msg_buscando = bot.send_message(chat_id, t['searching'], parse_mode="Markdown")

    try:
        res = t['results_for'].format(query=query_limpia)
        
        # --- VIP PROPIOS (Google Sheets) ---
        if config['show_vip']:
            try:
                r = requests.get(URL_SHEET)
                r.encoding = 'utf-8'
                csv_reader = list(csv.reader(StringIO(r.text)))
                
                mis_productos_vip = []
                for i, columnas in enumerate(csv_reader):
                    if i == 0 or len(columnas) < 3:
                        continue 
                    nombre = columnas[0].strip()
                    pais_excel = columnas[1].strip().upper()
                    link = columnas[2].strip()

                    # Acepta tanto "AR" como "ARGENTINA" escrito en tu Excel
                    if pais_excel in [pais_code.upper(), config['name'].upper()] and query_limpia in nombre.lower():
                        mis_productos_vip.append((nombre, link))
                
                if mis_productos_vip:
                    res += t['vip_local']
                    destacados = random.sample(mis_productos_vip, min(3, len(mis_productos_vip)))
                    for p_nombre, p_link in destacados:
                        res += f"💎 [{p_nombre}]({p_link})\n"
                    res += "\n"
            except Exception as e:
                print("Error leyendo Google Sheets:", e)

        # --- TIENDAS Y ENLACES ---
        res += t['stores']
        
        if config['show_ml']:
            dominio = config['ml_domain']
            tool_id = config['ml_tool']
            camp = config['ml_camp']
            res += f"{t['ml']}(https://listado.mercadolibre.{dominio}/{query_url_ml}?matt_tool={tool_id}&matt_word={camp})\n"
            
        if config['show_amz']:
            res += f"{t['amz']}(https://www.amazon.com/s?k={query_url_amz}&tag={AMAZON_TAG})\n"
            
        if config['show_ali']:
            busqueda_base = f"https://www.aliexpress.com/wholesale?SearchText={query_url_amz}"
            busqueda_codificada = urllib.parse.quote(busqueda_base, safe='')
            aliexpress_deep_link = f"https://s.click.aliexpress.com/deep_link.htm?aff_short_key={ALI_KEY}&dl_target_url={busqueda_codificada}"
            res += f"{t['ali']}({aliexpress_deep_link})\n"

        bot.edit_message_text(res, chat_id, msg_buscando.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        print("ERROR:", e)
        bot.edit_message_text(t['error_conn'], chat_id, msg_buscando.message_id)

# === 7. RUN ===
print("🔥 RADAR VIP ESTÁ EN LÍNEA: MENÚ COMPACTO Y VIP ARREGLADO...")
bot.remove_webhook()
bot.polling(none_stop=True)
