import streamlit as st
import easyocr
import numpy as np
from PIL import Image

# Конфигурация на страницата
st.set_page_config(page_title="Скенер за вредни съставки", layout="centered")

# Списък с вредни съставки (може да бъде разширен)
HARMFUL_INGREDIENTS = {
    "E621": "Мононатриев глутамат (Monosodium Glutamate) - овкусител, често свързван с главоболие.",
    "палмово масло": "Палмово масло (Palm Oil) - високо съдържание на наситени мазнини.",
    "palm oil": "Palm Oil - high saturated fat content.",
    "аспартам": "Аспартам (Aspartame) - изкуствен подсладител.",
    "aspartame": "Aspartame - artificial sweetener.",
    "нитрити": "Натриев нитрит (Sodium Nitrite) - консервант в колбасите.",
    "nitrite": "Sodium Nitrite - preservative used in cured meats.",
    "хидрогенирани": "Хидрогенирани мазнини - източник на транс-мазнини.",
    "hydrogenated": "Hydrogenated fats - source of trans fats."
    "Оцветители":
        'E102'
       ' Е104'
        'E110'
        'E122'
        'Е123'
       ' Е127'
        'Е131'
       ' E133'
        'Е151'
        
    "Консерванти":
        'Е211'
        'Е250'
        'Е220-Е228'
        
        "Подсладители и овкусители":
        'Е621'
        'Е951'
        'Е420'
        
        "Стабилизатори":
        'Е320'
        'Е321'
        'Е407'
        'Е450'
    "
}

# Инициализиране на OCR четеца (кешираме го, за да не се зарежда при всяко кликване)
@st.cache_resource
def load_ocr():
    # Зареждаме български и английски език
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

def scan_text(image):
    # Превръщаме PIL изображението в масив за EasyOCR
    img_array = np.array(image)
    results = reader.readtext(img_array, detail=0) # detail=0 връща само текста
    return " ".join(results).lower()

# Интерфейс
st.title("🛡️ Скенер за съставки")
st.write("Качете снимка на етикета, за да проверите за вредни добавки.")

# Опции за източник на снимка
source = st.radio("Изберете източник:", ("Качване на файл", "Камера"))

uploaded_file = None
if source == "Качване на файл":
    uploaded_file = st.file_uploader("Изберете снимка...", type=["jpg", "jpeg", "png"])
else:
    uploaded_file = st.camera_input("Направете снимка на етикета")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Вашата снимка', use_container_width=True)
    
    with st.spinner('Анализирам текста... моля изчакайте.'):
        # OCR обработка
        detected_text = scan_text(image)
        
        st.subheader("Разпознат текст:")
        with st.expander("Виж целия текст от етикета"):
            st.write(detected_text)
        
        # Проверка за вредни съставки
        found_bad_stuff = []
        for key, description in HARMFUL_INGREDIENTS.items():
            if key in detected_text:
                found_bad_stuff.append(description)
        
        # Резултати
        st.divider()
        if found_bad_stuff:
            st.warning("⚠️ Внимание! Намерени са потенциално вредни съставки:")
            for item in set(found_bad_stuff): # set() премахва дубликати
                st.write(f"- {item}")
        else:
            st.success("✅ Не бяха открити критични съставки от нашия списък.")

st.info("Забележка: Този софтуер е с информативна цел. Винаги четете етикетите внимателно.")
