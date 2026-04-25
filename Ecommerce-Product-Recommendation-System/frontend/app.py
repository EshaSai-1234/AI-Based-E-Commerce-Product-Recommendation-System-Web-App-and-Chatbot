# Import libraries
import streamlit as st
import requests
from pydantic import BaseModel
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
from io import BytesIO
import re

# Define the FastAPI endpoint URL
fastapi_url = "http://127.0.0.1:8000/"

def main():
    # Initialize Session State
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'last_results' not in st.session_state:
        st.session_state.last_results = {"answer": "", "products": []}
    
    LANGUAGES = {
        "Auto": "auto",
        "English": "en", "Spanish": "es", "French": "fr", "German": "de",
        "Hindi": "hi", "Bengali": "bn", "Marathi": "mr", "Telugu": "te",
        "Tamil": "ta", "Gujarati": "gu", "Kannada": "kn", "Malayalam": "ml",
        "Punjabi": "pa", "Arabic": "ar"
    }

    # Comprehensive 14-language localization dictionary
    LOCALIZATION = {
        "en": {
            "title": "AI-Based E-Commerce Product Recommendation System Web App and Chatbot",
            "manual_header": "🛍️ Search Products", "chatbot_header": "🤖 Shopping AI",
            "search_desc": "What are you looking for? (e.g. 'Laptop')",
            "placeholder": "Type keywords...", "voice_input": "Voice Search:",
            "get_rec": "Search Now", "top_k_label": "Max results:",
            "mode_manual": "Web App", "mode_chatbot": "Chatbot",
            "wait": "Finding best deals...", "warn_query": "Please enter a search term.",
            "chat_init": "Hi! How can I help you today? 😀 (Try: 'laptop above 4 rating')", "chat_input": "Message...",
            "add_to_cart": "🛒 Add to Cart", "cart_title": "🛒 Shopping Cart",
            "cart_empty": "Your cart is empty.", "total": "Total Amount:",
            "count": "Total Items:", "clear_cart": "Clear All",
            "added": "Added!", "delete": "🗑️", "rating": "Rating:",
            "min_rating": "Minimum Rating ⭐"
        },
        "es": {
            "title": "Sistema de recomendación de productos de comercio electrónico basado en IA",
            "manual_header": "🛍️ Buscar productos", "chatbot_header": "🤖 IA de compras",
            "search_desc": "¿Qué estás buscando? (ej. 'Laptop')",
            "placeholder": "Escribe palabras clave...", "voice_input": "Búsqueda por voz:",
            "get_rec": "Buscar ahora", "top_k_label": "Resultados máximos:",
            "mode_manual": "Aplicación web", "mode_chatbot": "Chatbot",
            "wait": "Buscando las mejores ofertas...", "warn_query": "Ingrese un término de búsqueda.",
            "chat_init": "¡Hola! ¿Cómo puedo ayudarte hoy? 😀", "chat_input": "Mensaje...",
            "add_to_cart": "🛒 Añadir al carrito", "cart_title": "🛒 Carrito de compras",
            "cart_empty": "Tu carrito está vacío.", "total": "Importe total:",
            "count": "Total de artículos:", "clear_cart": "Limpiar todo",
            "added": "¡Añadido!", "delete": "🗑️", "rating": "Calificación:",
            "min_rating": "Calificación mínima ⭐"
        },
        "fr": {
            "title": "Système de recommandation de produits e-commerce basé sur l'IA",
            "manual_header": "🛍️ Rechercher des produits", "chatbot_header": "🤖 IA de shopping",
            "search_desc": "Que cherchez-vous ? (ex. 'Ordinateur')",
            "placeholder": "Tapez des mots-clés...", "voice_input": "Recherche vocale :",
            "get_rec": "Rechercher maintenant", "top_k_label": "Résultats max :",
            "mode_manual": "Application Web", "mode_chatbot": "Chatbot",
            "wait": "Recherche des meilleures offres...", "warn_query": "Veuillez entrer un terme de recherche.",
            "chat_init": "Salut ! Comment puis-je t'aider aujourd'hui ? 😀", "chat_input": "Message...",
            "add_to_cart": "🛒 Ajouter au panier", "cart_title": "🛒 Panier",
            "cart_empty": "Votre panier est vide.", "total": "Montant total :",
            "count": "Total d'articles :", "clear_cart": "Tout effacer",
            "added": "Ajouté !", "delete": "🗑️", "rating": "Note :",
            "min_rating": "Note minimale ⭐"
        },
        "de": {
            "title": "KI-basiertes E-Commerce-Produktempfehlungssystem",
            "manual_header": "🛍️ Produkte suchen", "chatbot_header": "🤖 Shopping-KI",
            "search_desc": "Was suchen Sie? (z.B. 'Laptop')",
            "placeholder": "Schlagworte eingeben...", "voice_input": "Sprachsuche:",
            "get_rec": "Jetzt suchen", "top_k_label": "Max. Ergebnisse:",
            "mode_manual": "Web-App", "mode_chatbot": "Chatbot",
            "wait": "Beste Angebote finden...", "warn_query": "Bitte einen Suchbegriff eingeben.",
            "chat_init": "Hallo! Wie kann ich dir heute helfen? 😀", "chat_input": "Nachricht...",
            "add_to_cart": "🛒 In den Warenkorb", "cart_title": "🛒 Warenkorb",
            "cart_empty": "Dein Warenkorb ist leer.", "total": "Gesamtbetrag:",
            "count": "Anzahl Artikel:", "clear_cart": "Alles löschen",
            "added": "Hinzugefügt!", "delete": "🗑️", "rating": "Bewertung:",
            "min_rating": "Mindestbewertung ⭐"
        },
        "hi": {
            "title": "AI-आधारित ई-कॉमर्स उत्पाद अनुशंसा प्रणाली वेब ऐप और चैटबॉट",
            "manual_header": "🛍️ उत्पाद खोजें", "chatbot_header": "🤖 शॉपिंग एआई",
            "search_desc": "आप क्या खोज रहे हैं? (उदा. 'लैपटॉप')",
            "placeholder": "कीवर्ड लिखें...", "voice_input": "आवाज़ खोज:",
            "get_rec": "अभी खोजें", "top_k_label": "अधिकतम परिणाम:",
            "mode_manual": "वेब ऐप", "mode_chatbot": "चैटबॉट",
            "wait": "खोज की जा रही है...", "warn_query": "कृपया खोज शब्द दर्ज करें।",
            "chat_init": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ? 😀", "chat_input": "संदेश लिखें...",
            "add_to_cart": "🛒 कार्ट में जोड़ें", "cart_title": "🛒 शॉपिंग कार्ट",
            "cart_empty": "आपकी कार्ट खाली है।", "total": "कुल राशि:",
            "count": "कुल वस्तुएं:", "clear_cart": "सब साफ़ करें",
            "added": "जोड़ा गया!", "delete": "🗑️", "rating": "रेटिंग:",
            "min_rating": "न्यूनतम रेटिंग ⭐"
        },
        "bn": {
            "title": "এআই-ভিত্তিক ই-কমাৰ্চ পণ্য ৰিকমেন্ডেশন সিস্টেম",
            "manual_header": "🛍️ পণ্য খুঁজুন", "chatbot_header": "🤖 শপিং এআই",
            "search_desc": "আপনি কি খুঁজছেন? (উদা: 'ল্যাপটপ')",
            "placeholder": "কীওয়ার্ড লিখুন...", "voice_input": "ভয়েস সার্চ:",
            "get_rec": "এখনই খুঁজুন", "top_k_label": "সর্বোচ্চ ফলাফল:",
            "mode_manual": "ওয়েব অ্যাপ", "mode_chatbot": "চ্যাটবট",
            "wait": "সেরা ডিল খুঁজছি...", "warn_query": "অনুগ্রহ করে একটি সার্চ টার্ম লিখুন।",
            "chat_init": "হ্যালো! আজ আমি আপনাকে কিভাবে সাহায্য করতে পারি? 😀", "chat_input": "বার্তা লিখুন...",
            "add_to_cart": "🛒 কার্টে যোগ করুন", "cart_title": "🛒 শপিং কার্ট",
            "cart_empty": "আপনার কার্ট খালি।", "total": "মোট পরিমাণ:",
            "count": "মোট আইটেম:", "clear_cart": "সব মুছে ফেলুন",
            "added": "যোগ করা হয়েছে!", "delete": "🗑️", "rating": "রেটিং:",
            "min_rating": "নূন্যতম রেটিং ⭐"
        },
        "mr": {
            "title": "AI-आधारित ई-कॉमर्स उत्पादन शिफारस प्रणाली वेब अॅप आणि चॅटबॉट",
            "manual_header": "🛍️ उत्पादने शोधा", "chatbot_header": "🤖 शॉपिंग AI",
            "search_desc": "तुम्ही काय शोधत आहात? (उदा. 'लॅपटॉप')",
            "placeholder": "कीवर्ड टाइप करा...", "voice_input": "व्हॉइस सर्च:",
            "get_rec": "आता शोधा", "top_k_label": "जास्तीत जास्त निकाल:",
            "mode_manual": "वेब अॅप", "mode_chatbot": "चॅटबॉट",
            "wait": "सर्वोत्तम सौदे शोधत आहे...", "warn_query": "कृपया शोध शब्द प्रविष्ट करा.",
            "chat_init": "नमस्कार! मी आज तुम्हाला कशी मदत करू शकतो? 😀", "chat_input": "संदेश...",
            "add_to_cart": "🛒 कार्टमध्ये जोडा", "cart_title": "🛒 शॉपिंग कार्ट",
            "cart_empty": "तुमची कार्ट रिकामी आहे.", "total": "एकूण रक्कम:",
            "count": "एकूण वस्तू:", "clear_cart": "सर्व साफ करा",
            "added": "जोडले!", "delete": "🗑️", "rating": "रेटिंग:",
            "min_rating": "किमान रेटिंग ⭐"
        },
        "te": {
            "title": "AI- ఆధారిత ఇ-కామర్స్ ఉత్పత్తి సిఫార్సు సిస్టమ్ వెబ్ యాప్ మరియు చాట్‌బాట్",
            "manual_header": "🛍️ ఉత్పత్తులను వెతకండి", "chatbot_header": "🤖 షాపింగ్ AI",
            "search_desc": "మీరు ఏమి వెతుకుతున్నారు? (ఉదా. 'ల్యాప్‌టాప్')",
            "placeholder": "కీవర్డ్‌లను టైప్ చేయండి...", "voice_input": "వాయిస్ సెర్చ్:",
            "get_rec": "ఇప్పుడే వెతకండి", "top_k_label": "గరిష్ట ఫలితాలు:",
            "mode_manual": "వెబ్ యాప్", "mode_chatbot": "చాట్‌బాట్",
            "wait": "ఉత్తమ డీల్స్ కోసం వెతుకుతోంది...", "warn_query": "దయచేసి సెర్చ్ పదాన్ని నమోదు చేయండి.",
            "chat_init": "హలో! ఈ రోజు నేను మీకు ఎలా సహాయపడగలను? 😀", "chat_input": "సందేశం...",
            "add_to_cart": "🛒 కార్ట్‌కు జోడించు", "cart_title": "🛒 షాపింగ్ కార్ట్",
            "cart_empty": "మీ కార్ట్ ఖాళీగా ఉంది.", "total": "మొత్తం ధర:",
            "count": "మొత్తం వస్తువులు:", "clear_cart": "అన్నీ క్లియర్ చేయండి",
            "added": "జోడించబడింది!", "delete": "🗑️", "rating": "రేటింగ్:",
            "min_rating": "కనిష్ట రేటింగ్ ⭐"
        },
        "ta": {
            "title": "AI-அடிப்படையிலான இ-காமர்ஸ் தயாரிப்பு பரிந்துரை அமைப்பு",
            "manual_header": "🛍️ தயாரிப்புகளைத் தேடுங்கள்", "chatbot_header": "🤖 ஷாப்பிங் AI",
            "search_desc": "நீங்கள் எதைத் தேடுகிறீர்கள்? (எ.கா. 'லேப்டாப்')",
            "placeholder": "முக்கிய வார்த்தைகளைத் தட்டச்சு செய்க...", "voice_input": "குரல் தேடல்:",
            "get_rec": "இப்போதே தேடு", "top_k_label": "அதிகபட்ச முடிவுகள்:",
            "mode_manual": "வலைப் பயன்பாடு", "mode_chatbot": "சாட்போட்",
            "wait": "சிறந்த டீல்களைத் தேடுகிறது...", "warn_query": "தேடல் சொல்லை உள்ளிடவும்.",
            "chat_init": "வணக்கம்! இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்? 😀", "chat_input": "செய்தி...",
            "add_to_cart": "🛒 கார்ட்டில் சேர்", "cart_title": "🛒 ஷாப்பிங் கார்ட்",
            "cart_empty": "உங்கள் கார்ட் காலியாக உள்ளது.", "total": "மொத்தத் தொகை:",
            "count": "மொத்த பொருட்கள்:", "clear_cart": "அனைத்தையும் நீக்கு",
            "added": "சேர்க்கப்பட்டது!", "delete": "🗑️", "rating": "மதிப்பீடு:",
            "min_rating": "குறைந்தபட்ச மதிப்பீடு ⭐"
        },
        "gu": {
            "title": "AI-આધારિત ઈ-કોમર્સ પ્રોડક્ટ રિકમેન્ડેશન સિસ્ટમ વેબ એપ અને ચેટબોટ",
            "manual_header": "🛍️ ઉત્પાદનો શોધો", "chatbot_header": "🤖 શોપિંગ AI",
            "search_desc": "તમે શું શોધી રહ્યા છો? (દા.ત. 'લેપટોપ')",
            "placeholder": "કીવર્ડ લખો...", "voice_input": "વોઈસ સર્ચ:",
            "get_rec": "હમણાં શોધો", "top_k_label": "મહત્તમ પરિણામો:",
            "mode_manual": "વેબ એપ", "mode_chatbot": "ચેટબોટ",
            "wait": "શ્રેષ્ઠ સોદા શોધી રહ્યા છીએ...", "warn_query": "કૃપા કરીને સર્ચ શબ્દ દાખલ કરો.",
            "chat_init": "નમસ્તે! હું આજે તમને કેવી રીતે મદદ કરી શકું? 😀", "chat_input": "સંદેશ...",
            "add_to_cart": "🛒 કાર્ટમાં ઉમેરો", "cart_title": "🛒 શોપિંગ કાર્ટ",
            "cart_empty": "તમારું કાર્ટ ખાલી છે.", "total": "કુલ રકમ:",
            "count": "કુલ વસ્તુઓ:", "clear_cart": "બધું સાફ કરો",
            "added": "ઉમેરાયું!", "delete": "🗑️", "rating": "રેટિંગ:",
            "min_rating": "લઘુત્તમ રેટિંગ ⭐"
        },
        "kn": {
            "title": "AI-ಆಧಾರಿತ ಇ-ಕಾಮರ್ಸ್ ಉತ್ಪನ್ನ ಶಿಫಾರಸು ವ್ಯವಸ್ಥೆ",
            "manual_header": "🛍️ ಉತ್ಪನ್ನಗಳನ್ನು ಹುಡುಕಿ", "chatbot_header": "🤖 ಶಾಪಿಂಗ್ AI",
            "search_desc": "ನೀವು ಏನು ಹುಡುಕುತ್ತಿದ್ದೀರಿ? (ಉದಾ. 'ಲ್ಯಾಪ್ಟಾಪ್')",
            "placeholder": "ಕೀವರ್ಡ್‌ಗಳನ್ನು ಟೈಪ್ ಮಾಡಿ...", "voice_input": "ಧ್ವನಿ ಹುಡುಕಾಟ:",
            "get_rec": "ಈಗ ಹುಡುಕಿ", "top_k_label": "ಗರಿಷ್ಠ ಫಲಿತಾಂಶಗಳು:",
            "mode_manual": "ವೆಬ್ ಅಪ್ಲಿಕೇಶನ್", "mode_chatbot": "ಚಾಟ್‌ಬಾಟ್",
            "wait": "ಅತ್ಯುತ್ತಮ ಡೀಲ್‌ಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ...", "warn_query": "ಹುಡುಕಾಟ ಪದವನ್ನು ನಮೂದಿಸಿ.",
            "chat_init": "ನಮಸ್ಕಾರ! ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ? 😀", "chat_input": "ಸಂದೇಶ...",
            "add_to_cart": "🛒 ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಿ", "cart_title": "🛒 ಶಾಪಿಂಗ್ ಕಾರ್ಟ್",
            "cart_empty": "ನಿಮ್ಮ ಕಾರ್ಟ್ ಖಾಲಿಯಾಗಿದೆ.", "total": "ಒಟ್ಟು ಮೊತ್ತ:",
            "count": "ಒಟ್ಟು ವಸ್ತುಗಳು:", "clear_cart": "ಎಲ್ಲವನ್ನೂ ತೆರವುಗೊಳಿಸಿ",
            "added": "ಸೇರಿಸಲಾಗಿದೆ!", "delete": "🗑️", "rating": "ರೇಟಿಂಗ್:",
            "min_rating": "ಕನಿಷ್ಠ ರೇಟಿಂಗ್ ⭐"
        },
        "ml": {
            "title": "AI-അധിഷ്ഠിത ഇ-കൊമേഴ്‌സ് ഉൽപ്പന്ന ശുപാർശ സംവിധാനം",
            "manual_header": "🛍️ ഉൽപ്പന്നങ്ങൾ തിരയുക", "chatbot_header": "🤖 ഷോപ്പിംഗ് AI",
            "search_desc": "നിങ്ങൾ എന്താണ് തിരയുന്നത്? (ഉദാ. 'ലാപ്ടോപ്പ്')",
            "placeholder": "കീവേഡുകൾ ടൈപ്പ് ചെയ്യുക...", "voice_input": "വോയ്‌സ് സെർച്ച്:",
            "get_rec": "ഇപ്പോൾ തിരയുക", "top_k_label": "പരമാവധി ഫലങ്ങൾ:",
            "mode_manual": "വെബ് ആപ്പ്", "mode_chatbot": "ചാറ്റ്ബോട്ട്",
            "wait": "മികച്ച ഡീലുകൾ കണ്ടെത്തുന്നു...", "warn_query": "തിരയൽ പദം നൽകുക.",
            "chat_init": "ഹലോ! ഇന്ന് എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാനാകും? 😀", "chat_input": "സന്ദേശം...",
            "add_to_cart": "🛒 കാർട്ടിലേക്ക് ചേർക്കുക", "cart_title": "🛒 ഷോപ്പിംഗ് കാർട്ട്",
            "cart_empty": "നിങ്ങളുടെ കാർട്ട് ശൂന്യമാണ്.", "total": "ആകെ തുക:",
            "count": "ആകെ ഇനങ്ങൾ:", "clear_cart": "എല്ലാം ഒഴിവാക്കുക",
            "added": "ചേർത്തു!", "delete": "🗑️", "rating": "റേറ്റിംഗ്:",
            "min_rating": "കുറഞ്ഞ റേറ്റിംഗ് ⭐"
        },
        "pa": {
            "title": "AI-ਅਧਾਰਿਤ ਈ-ਕਾਮਰਸ ਉਤਪਾਦ ਸਿਫਾਰਸ਼ ਸਿਸਟਮ",
            "manual_header": "🛍️ ਉਤਪਾਦ ਖੋਜੋ", "chatbot_header": "🤖 ਸ਼ਾਪਿੰਗ AI",
            "search_desc": "ਤੁਸੀਂ ਕੀ ਲੱਭ ਰਹੇ ਹੋ? (ਉਦਾਹਰਨ ਲਈ 'ਲੈਪਟਾਪ')",
            "placeholder": "ਕੀਵਰਡ ਟਾਈਪ ਕਰੋ...", "voice_input": "ਆਵਾਜ਼ ਖੋਜ:",
            "get_rec": "ਹੁਣੇ ਖੋਜੋ", "top_k_label": "ਅਧਿਕਤਮ ਨਤੀਜੇ:",
            "mode_manual": "ਵੈੱਬ ਐਪ", "mode_chatbot": "ਚੈਟਬੋਟ",
            "wait": "ਸਭ ਤੋਂ ਵਧੀਆ ਸੌਦੇ ਲੱਭ ਰਹੇ ਹੋ...", "warn_query": "ਕਿਰਪਾ ਕਰਕੇ ਖੋਜ ਸ਼ਬਦ ਦਰਜ ਕਰੋ।",
            "chat_init": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ? 😀", "chat_input": "ਸੁਨੇਹਾ...",
            "add_to_cart": "🛒 ਕਾਰਟ ਵਿੱਚ ਸ਼ਾਮਲ ਕਰੋ", "cart_title": "🛒 ਸ਼ਾਪਿੰਗ ਕਾਰਟ",
            "cart_empty": "ਤੁਹਾਡੀ ਕਾਰਟ ਖਾਲੀ ਹੈ।", "total": "ਕੁੱਲ ਰਕਮ:",
            "count": "ਕੁੱਲ ਵਸਤੂਆਂ:", "clear_cart": "ਸਭ ਸਾਫ਼ ਕਰੋ",
            "added": "ਸ਼ਾਮਲ ਕੀਤਾ ਗਿਆ!", "delete": "🗑️", "rating": "ਰੇਟਿੰਗ:",
            "min_rating": "ਘੱਟੋ-ਘੱਟ ਰੇਟਿੰਗ ⭐"
        },
        "ar": {
            "title": "نظام توصية منتجات التجارة الإلكترونية القائم على الذكاء الاصطناعي",
            "manual_header": "🛍️ البحث عن المنتجات", "chatbot_header": "🤖 ذكاء التسوق الاصطناعي",
            "search_desc": "ماذا تبحث عن؟ (مثلاً 'لابتوب')",
            "placeholder": "اكتب الكلمات المفتاحية...", "voice_input": "البحث الصوتي:",
            "get_rec": "ابحث الآن", "top_k_label": "أقصى عدد من النتائج:",
            "mode_manual": "تطبيق الويب", "mode_chatbot": "روبوت الدردشة",
            "wait": "البحث عن أفضل العروض...", "warn_query": "يُرجى إدخال كلمة بحث.",
            "chat_init": "مرحباً! كيف يمكنني مساعدتك اليوم؟ 😀", "chat_input": "رسالة...",
            "add_to_cart": "🛒 أضف إلى السلة", "cart_title": "🛒 سلة التسوق",
            "cart_empty": "سلة التسوق فارغة.", "total": "المبلغ الإجمالي:",
            "count": "إجمالي القطع:", "clear_cart": "مسح الكل",
            "added": "تمت الإضافة!", "delete": "🗑️", "rating": "التقييم:",
            "min_rating": "الحد الأدنى للتقييم ⭐"
        }
    }

    for l_key in LANGUAGES.values():
        if l_key not in LOCALIZATION:
             LOCALIZATION[l_key] = LOCALIZATION["en"]

    st.sidebar.title("Settings ⚡")
    selected_language = st.sidebar.selectbox("Language 🌐", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[selected_language]
    voice_lang_code = "en" if selected_language == "Auto" else lang_code
    texts = LOCALIZATION.get(lang_code, LOCALIZATION["en"])
    
    st.title(texts["title"])
    enable_audio = st.sidebar.checkbox("🔊 Audio Enable")
    
    # Global Rating Filter
    min_rating = st.sidebar.slider(texts["min_rating"], 0.0, 5.0, 0.0, 0.1)

    # Cart UI
    st.sidebar.markdown("---")
    st.sidebar.header(texts["cart_title"])
    cart_items = st.session_state.cart
    if not cart_items:
        st.sidebar.info(texts["cart_empty"])
    else:
        st.sidebar.write(f"**{texts['count']}** {len(cart_items)}")
        total_val = 0
        for i, item in enumerate(cart_items):
            c1, c2 = st.sidebar.columns([4, 1])
            with c1:
                st.write(f"{item['name']} (₹{int(float(item['price'])):,})")
            with c2:
                if st.button(texts["delete"], key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            total_val += int(float(item['price']))
        st.sidebar.markdown("---")
        st.sidebar.subheader(f"{texts['total']} ₹{total_val:,}")
        if st.sidebar.button(texts["clear_cart"]):
            st.session_state.cart = []
            st.rerun()

    def clean_text_for_tts(text):
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'[#\*]+', ' ', text)
        return text[:400]

    def play_audio(text, lang='en'):
        if not enable_audio: return
        try:
            tts = gTTS(text=clean_text_for_tts(text), lang=lang)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            st.audio(fp, format="audio/mp3", autoplay=True)
        except Exception as e: st.error(f"TTS Error: {e}")

    def render_product_cards(products, key_prefix=""):
        if not products: return
        for i, p in enumerate(products):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{p.get('product_name')}**")
                    st.caption(p.get('product_features', ''))
                    r = p.get('rating', '0')
                    st.write(f"{texts['rating']} **{r} ⭐**")
                    st.write(f"Price: **₹{int(float(p.get('price', 0))):,}**")
                with col2:
                    # Use both product_id and index/prefix to ensure global uniqueness
                    btn_key = f"{key_prefix}btn_{p.get('product_id')}_{i}"
                    if st.button(texts["add_to_cart"], key=btn_key):
                        st.session_state.cart.append({'id': p.get('product_id'), 'name': p.get('product_name'), 'price': p.get('price')})
                        st.toast(texts["added"])
                        st.rerun()

    def manual():
        st.header(texts['manual_header'])
        query = st.text_area(texts['search_desc'], placeholder=texts['placeholder'], height=100)
        stt_text = speech_to_text(language=voice_lang_code, use_container_width=True, just_once=True, key='STT_manual')
        if stt_text: query = stt_text
        top_k = st.number_input(texts['top_k_label'], min_value=1, value=5)
        if st.button(texts['get_rec']):
            if not query: st.warning(texts['warn_query'])
            else:
                with st.spinner(texts['wait']):
                    try:
                        r = requests.post(fastapi_url +"/chatbot", json={'query': query, 'top_k': top_k, 'min_rating': min_rating, 'language': selected_language})
                        if r.status_code == 200:
                            st.session_state.last_results = r.json()
                            play_audio(st.session_state.last_results['answer'], lang=voice_lang_code)
                        else:
                            st.error(f"Backend Error: {r.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("Backend is still initializing or disconnected. Please wait a moment and try again.")
        if st.session_state.last_results['answer']:
            st.markdown(st.session_state.last_results['answer'])
            render_product_cards(st.session_state.last_results['products'], key_prefix="manual_")

    def chatbot():
        st.header(texts['chatbot_header'])
        if "Messages" not in st.session_state:
            st.session_state["Messages"] = [{"actor": "Assistant", "payload": texts['chat_init'], "products": []}]
        for idx, msg in enumerate(st.session_state["Messages"]):
            with st.chat_message(msg["actor"]):
                st.write(msg["payload"])
                if msg["products"]: render_product_cards(msg["products"], key_prefix=f"chat_{idx}_")
        prompt = st.chat_input(texts['chat_input'])
        stt_prompt = speech_to_text(language=voice_lang_code, use_container_width=True, just_once=True, key='STT_chat')
        if stt_prompt: prompt = stt_prompt
        if prompt:
            st.session_state["Messages"].append({"actor": "User", "payload": prompt, "products": []})
            with st.chat_message("User"): st.write(prompt)
            with st.spinner(texts['wait']):
                try:
                    r = requests.post(fastapi_url +"/chatbot", json={"query": prompt, "top_k": 3, "min_rating": min_rating, "language": selected_language})
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state["Messages"].append({"actor": "Assistant", "payload": data['answer'], "products": data['products']})
                        with st.chat_message("Assistant"):
                            st.write(data['answer'])
                            # The last message is already in st.session_state["Messages"] but we render it here for immediate feedback
                            # We use a special prefix to avoid collision with the history loop above
                            render_product_cards(data['products'], key_prefix="new_")
                        play_audio(data['answer'], lang=voice_lang_code)
                    else:
                        st.error(f"Backend Error: {r.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend is still initializing or disconnected. Please wait a moment and try again.")

    mode = st.sidebar.radio("Navigation", [texts['mode_manual'], texts['mode_chatbot']])
    if mode == texts['mode_manual']: manual()
    else: chatbot()
   
if __name__ == '__main__':
    main()
