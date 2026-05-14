import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Конфигурация на страницата
st.set_page_config(page_title="Скенер за вредни съставки", layout="centered")

# РАЗШИРЕН СПИСЪК СЪС СЪСТАВКИ
# Ключовете са нормализирани (Латинско E, без интервали)
HARMFUL_INGREDIENTS = {
    # Оцветители
    "E102": "Тартразин (Оцветител) - може да предизвика алергични реакции.",
    "E104": "Хинолиново жълто (Оцветител) - забранено в някои страни.",
    "E110": "Сънсет жълто (Оцветител) - риск от хиперактивност при деца.",
    "E120": "Кармин/Корнихил (Естествен оцветител, но потенциален алерген).",
    "E122": "Азорубин (Оцветител) - синтетичен червен оцветител.",
    "E123": "Амарант (Оцветител) - силно ограничен за употреба.",
    "E127": "Еритрозин (Оцветител) - съдържа йод, влияе на щитовидната жлеза.",
    "E131": "Патент синьо V (Оцветител).",
    "E133": "Брилянтно синьо (Оцветител).",
    "E151": "Брилянтно черно (Оцветител).",
    
    # Консерванти
    "E211": "Натриев бензоат (Консервант) - избягвайте в комбинация с витамин С.",
    "E250": "Натриев нитрит (Консервант) - често срещан в колбасите.",
    "E220": "Серен диоксид (Консервант/Антиоксидант).",
    "E221": "Натриев сулфит.",
    "E222": "Натриев хидрогенсулфит.",
    "E223": "Натриев метабисулфит.",
    "E224": "Калиев метабисулфит.",
    "E225": "Калиев сулфит.",
    "E226": "Калциев сулфит.",
    "E227": "Калциев хидрогенсулфит.",
    "E228": "Калиев хидрогенсулфит.",
    "E316": "Натриев ериторбат.",
    
    # Стабилизатори и емулгатори
    "E407A": "Карагенан - потенциален дразнител на стомаха.",
    "E412": "Гума гуар - сгъстител.",
    
    # Подсладители и овкусители
    "E621": "Мононатриев глутамат - овкусител, свързван с главоболие.",
    "E951": "Аспартам - изкуствен подсладител.",
    "E420": "Сорбитол - подсладител, в големи дози има слабително действие.",
    "АСПАРТАМ": "Аспартам (Aspartame) - изкуствен подсладител.",
    "ASPARTAME": "Aspartame - artificial sweetener.",
    
    # Мазнини
    "ПАЛМОВО МАСЛО": "Палмово масло (Palm Oil) - високо съдържание на наситени мазнини.",
    "PALM OIL": "Palm Oil - high saturated fat content.",
    "ХИДРОГЕНИРАНИ": "Хидрогенирани мазнини - източник на вредни транс-мазнини.",
    "HYDROGENATED": "Hydrogenated fats - source of trans fats."
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

def preprocess_text(text_list):
    # Обединяваме всичко в един низ
    full_text = " ".join(text_list).upper()
    
    # 1. Сменяме кирилско 'Е' с латинско 'E'
    full_text = full_text.replace("Е", "E")
    
    # 2. Оправяме често срещана грешка: О (буква) вместо 0 (цифра) в Е-номерата
    # Търсим буква E, следвана от цифри, където може да има O
    full_text = re.sub(r'(?<=E)\d*O\d*', lambda m: m.group(0).replace('O', '0'), full_text)
    
    # 3. Премахваме интервалите между 'E' и цифрите (напр. 'E 102' -> 'E102')
    full_text = re.sub(r'E\s+', 'E', full_text)
    
    return full_text

# Интерфейс
st.title("🛡️ Скенер за съставки")
st.write("Качете снимка на етикета за проверка.")

source = st.radio("Изберете източник:", ("Качване на файл", "Камера"))

uploaded_file = None
if source == "Качване на файл":
    uploaded_file = st.file_uploader("Изберете снимка...", type=["jpg", "jpeg", "png"])
else:
    uploaded_file = st.camera_input("Направете снимка")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    with st.spinner('Анализирам текста...'):
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0)
        
        # Обработка на текста за по-добро засичане
        clean_text = preprocess_text(results)
        
        st.subheader("Разпознат текст:")
        with st.expander("Виж извлечените данни"):
            st.write(clean_text)
        
        # Проверка
        found_bad_stuff = []
        for key, description in HARMFUL_INGREDIENTS.items():
            if key in clean_text:
                found_bad_stuff.append(description)
        
        st.divider()
        if found_bad_stuff:
            st.warning("⚠️ Внимание! Намерени са съставки:")
            for item in sorted(set(found_bad_stuff)):
                st.write(f"- {item}")
        else:
            st.success("✅ Не бяха открити критични съставки.")
