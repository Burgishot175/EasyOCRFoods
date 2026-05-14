import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Настройка на страницата
st.set_page_config(page_title="🛡️ Скенер за съставки", layout="centered")

# ОБНОВЕНА БАЗА ДАННИ
INGREDIENT_DATABASE = {
    # --- ОЦВЕТИТЕЛИ ---
    "E102": "Тартразин - жълт оцветител, възможен алерген.",
    "E104": "Хинолиново жълто - забранен в някои страни.",
    "E110": "Сънсет жълто - риск от хиперактивност при деца.",
    "E122": "Азорубин - синтетичен червен оцветител.",
    "E123": "Амарант - силно ограничена употреба.",
    "E127": "Еритрозин - съдържа йод, влияе на щитовидната жлеза.",
    "E131": "Патент синьо V - синтетичен оцветител.",
    "E133": "Брилянтно синьо - синтетичен оцветител.",
    "E151": "Брилянтно черно BN - синтетичен оцветител.",
    "E120": "Кармин/Кошенил - извлечен от насекоми, силен алерген.",

    # --- КОНСЕРВАНТИ ---
    "E211": "Натриев бензоат - избягвайте с витамин С.",
    "E250": "Натриев нитрит - използва се в колбаси, потенциален карциноген.",
    "E220": "Серен диоксид - сулфит, силен алерген.",
    "E221": "Натриев сулфит.",
    "E222": "Натриев хидрогенсулфит.",
    "E223": "Натриев метабисулфит.",
    "E224": "Калиев метабисулфит.",
    "E225": "Калиев сулфит.",
    "E226": "Калциев сулфит.",
    "E227": "Калциев хидрогенсулфит.",
    "E228": "Калиев хидрогенсулфит.",

    # --- ПОДСЛАДИТЕЛИ И ОВКУСИТЕЛИ ---
    "E621": "Мононатриев глутамат - овкусител, причинява главоболие.",
    "E951": "Аспартам - изкуствен подсладител.",
    "E420": "Сорбитол - подсладител, слабително действие в големи дози.",

    # --- ВРЕДНИ СЪСТАВКИ (ТЕКСТ) ---
    "МАЛТОДЕКСТРИН": "Малтодекстрин - висок гликемичен индекс.",
    "МАЛТОДЕКАТРИН": "Малтодекстрин (засечен с грешка) - висок гликемичен индекс.", # Грешката от image_b08dd6.png
    "MALLODEXTRIN": "Maltodextrin (detected error) - high glycemic index.", # Грешката от image_b08dd6.png
    "ПАЛМОВО": "Палмово масло/мазнина - високо съдържание на наситени мазнини.",
    "ХИДРОГЕНИРАНИ": "Хидрогенирани мазнини - източник на транс-мазнини.",
    "ЗАХАР": "Внимание: Високо съдържание на захар.",
    "ГЛУТАМАТ": "Глутамат - овкусител.",
    "АСПАРТАМ": "Аспартам - подсладител."
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

def normalize_text(text_list):
    raw_text = " ".join(text_list).upper()
    
    # 1. Поправка за Е-номера (Латиница)
    # Сменяме €, кирилско Е и грешни символи
    text_for_e = raw_text.replace("Е", "E").replace("€", "E").replace("I", "1").replace("L", "1")
    # Оправяме O вместо 0 (напр. Е4O7)
    text_for_e = re.sub(r'(?<=E\d)O|O(?=\d)', '0', text_for_e)
    
    # 2. Поправка за думи (Кирилица)
    # Превръщаме визуално еднакви латински букви в кирилски
    caps = {'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н', 'O': 'О', 'P': 'Р', 'C': 'С', 'T': 'Т', 'X': 'Х', 'Y': 'У'}
    text_for_words = raw_text
    for lat, cyr in caps.items():
        text_for_words = text_for_words.replace(lat, cyr)
    
    return text_for_e, text_for_words

def scan_for_ingredients(text_for_e, text_for_words):
    found = {}
    
    # Търсене на Е-номера (Regex)
    e_pattern = re.compile(r'E\s*(\d+)([A-Z]?)')
    e_matches = e_pattern.findall(text_for_e)
    for match in e_matches:
        code = "E" + match[0] + match[1]
        if code in INGREDIENT_DATABASE:
            found[code] = INGREDIENT_DATABASE[code]

    # Търсене на думи и части от думи
    combined_text = text_for_words + " " + text_for_words.replace(" ", "")
    for key, desc in INGREDIENT_DATABASE.items():
        if not key.startswith("E") or len(key) > 4: # Търси думи или сложни Е-номера
            if key in combined_text:
                found[key] = desc
                
    return found

# ИНТЕРФЕЙС
st.title("🛡️ Скенер за съставки")

uploaded_file = st.file_uploader("Качете снимка на етикет", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, use_container_width=True)
    
    with st.spinner('Анализиране...'):
        results = reader.readtext(np.array(img), detail=0)
        t_e, t_w = normalize_text(results)
        found = scan_for_ingredients(t_e, t_w)
        
        with st.expander("Виж разчетения текст"):
            st.write(t_w)
        
        st.divider()
        if found:
            st.warning("⚠️ Открити вредни съставки:")
            for item, desc in found.items():
                st.write(f"- **{item}**: {desc}")
        else:
            st.success("✅ Не са открити критични съставки.")
