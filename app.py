import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Настройка на страницата
st.set_page_config(page_title="🛡️ Скенер за съставки", layout="centered")

# БАЗА ДАННИ (Е-номера и ключови думи)
# Ключовете трябва да са с ГЛАВНИ БУКВИ за по-лесна проверка
INGREDIENT_DATABASE = {
    # Оцветители
    "E102": "Тартразин (Оцветител) - може да предизвика алергии.",
    "E104": "Хинолиново жълто (Оцветител) - силно ограничен.",
    "E110": "Сънсет жълто FCF (Оцветител).",
    "E120": "Кармин/Кошенил (E120) - оцветител от насекоми, силен алерген.",
    "E122": "Азорубин (Оцветител).",
    "E250": "Натриев нитрит (E250) - консервант за месо, карциноген.",
    "E316": "Натриев ериторбат (E316) - антиоксидант.",

    # Стабилизатори и вредни думи
    "E407": "Карагенан (E407) - риск от възпаление на червата.",
    "E407A": "Преработени морски водорасли Euchema (E407a) - стабилизатор.",
    "E412": "Гума гуар (E412) - сгъстител, възможен алерген.",
    "E621": "Мононатриев глутамат (E621) - овкусител.",
    "E951": "Аспартам (Подсладител).",
    
    # Ключови думи (Текст)
    "МАЛТОДЕКСТРИН": "Малтодекстрин - въглехидрат, който рязко покачва кръвната захар.",
    "ПАЛМОВО МАСЛО": "Палмово масло - високо съдържание на наситени мазнини.",
    "ПАЛМОВА МАЗНИНА": "Палмова мазнина - високо съдържание на наситени мазнини.",
    "ХИДРОГЕНИРАНИ": "Хидрогенирани мазнини - източник на транс-мазнини.",
    "АСПАРТАМ": "Аспартам - изкуствен подсладител.",
    "ГЛУТАМАТ": "Глутамат - мощен овкусител, често свързван с главоболие.",
    "ЗАХАР": "Внимание: Високо съдържание на захар.",
    "НИТРИТ": "Нитрити - консерванти, потенциално карциногенни."
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

def process_text_and_find_ingredients(text_list):
    # 1. Обединяваме и нормализираме текста
    full_text = " ".join(text_list).upper()
    
    # Почистване на символи, които OCR бърка
    clean_text = full_text.replace("Е", "E").replace("€", "E")
    
    # СЪЗДАВАМЕ ВТОРА ВЕРСИЯ на текста без никакви интервали за търсене на думи
    # Това помага, ако OCR е разчел "МАЛТО ДЕКСТРИН" с интервал по средата
    text_no_spaces = clean_text.replace(" ", "")

    found_results = {}

    # --- ТЪРСЕНЕ НА Е-НОМЕРА (Regex) ---
    e_pattern = re.compile(r'E\s*(\d+)([A-Z]?)')
    e_matches = e_pattern.findall(clean_text)
    for match in e_matches:
        code = "E" + match[0] + match[1]
        if code in INGREDIENT_DATABASE:
            found_results[code] = INGREDIENT_DATABASE[code]

    # --- ТЪРСЕНЕ НА ТЕКСТОВИ СЪСТАВКИ ---
    for key in INGREDIENT_DATABASE:
        if not key.startswith("E"): # Търсим само думите
            # Проверяваме в нормалния текст И в текста без интервали
            if key in clean_text or key in text_no_spaces:
                found_results[key] = INGREDIENT_DATABASE[key]

    return found_results, clean_text

# --- ИНТЕРФЕЙС ---
st.title("🛡️ Пълен скенер за съставки")
st.write("Качете снимка на етикета, за да за засечете Е-номера и вредни съставки (Малтодекстрин, мазнини и др.).")

uploaded_file = st.file_uploader("Изберете снимка...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    with st.spinner('Анализирам текста...'):
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0)
        
        found_ingredients, processed_text = process_text_and_find_ingredients(results)

        # Дебъг информация
        with st.expander("Виж разпознатия текст"):
            st.write(processed_text)

        st.divider()

        if found_ingredients:
            st.warning("⚠️ Внимание! Открити са следните съставки:")
            for item, desc in found_ingredients.items():
                st.write(f"- **{item}**: {desc}")
        else:
            st.success("✅ Не бяха открити критични съставки от базата данни.")

st.info("Съвет: Списъкът може да се допълва с нови думи в речника на програмата.")
