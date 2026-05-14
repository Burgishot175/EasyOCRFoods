import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Настройка на страницата
st.set_page_config(page_title="🛡️ Скенер за вредни съставки Е-номера", layout="centered")

# РАЗШИРЕН СПИСЪК СЪС СЪСТАВКИ ЗА ПРОВЕРКА (Ключовете са чисти Е-номера)
INGREDIENT_DATABASE = {
    # Оцветители
    "E102": "Тартразин (Оцветител) - може да предизвика алергии.",
    "E104": "Хинолиново жълто (Оцветител) - силно ограничен.",
    "E110": "Сънсет жълто FCF (Оцветител).",
    "E120": "Кармин/Кошенил (E120) - оцветител от насекоми, силен алерген.",
    "E122": "Азорубин (Оцветител).",
    "E124": "Понсо 4R (Оцветител).",
    "E127": "Еритрозин (Оцветител) - съдържа йод.",
    "E129": "Алура червено AC (Оцветител).",
    "E131": "Патент синьо V (Оцветител).",
    "E132": "Индиго кармин (Оцветител).",
    "E133": "Брилянтно синьо FCF (Оцветител).",
    "E151": "Брилянтно черно BN (Оцветител).",
    
    # Консерванти
    "E200": "Сорбинова киселина (Консервант).",
    "E202": "Калиев сорбат (Консервант).",
    "E211": "Натриев бензоат (Консервант) - риск в комбинация с Вит. С.",
    "E220": "Серен диоксид (Консервант) - сулфит, алерген.",
    "E250": "Натриев нитрит (E250) - консервант за месо, карциноген.",
    "E316": "Натриев ериторбат (E316) - антиоксидант.",

    # Стабилизатори и емулгатори
    "E407": "Карагенан (E407) - риск от възпаление на червата.",
    "E407A": "Преработени морски водорасли Euchema (E407a) - стабилизатор.",
    "E412": "Гума гуар (E412) - сгъстител, възможен алерген.",
    
    # Овкусители и подсладители
    "E621": "Мононатриев глутамат (E621) - овкусител.",
    "E951": "Аспартам (Подсладител).",
}

@st.cache_resource
def load_ocr():
    # Зареждаме само 'bg' и 'en'
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_ocr()

def extract_and_clean_e_numbers(text_list):
    # Обединяваме и почистваме текста агресивно
    full_text = " ".join(text_list)
    # Поправяме най-честите OCR грешки преди да търсим
    full_text = full_text.upper()
    full_text = full_text.replace("Е", "E") # Кирилица -> Латиница
    full_text = full_text.replace("€", "E") # Евро символ -> Е
    full_text = full_text.replace("I", "1") # Буква I -> 1 (ако се появи в Е-номер)
    full_text = full_text.replace("L", "1") # Буква L -> 1

    # Регулярен израз за откриване на модел за Е-номер:
    # 1. Започва с 'E'
    # 2. Може да има интервали (\s*)
    # 3. Един или повече цифри (\d+)
    # 4. Може да има незадължителна буква след това ([A-Z]?)
    # 5. Специално за E407a: Оправяме грешката O вместо 0 (E4O7A -> E407A)
    cleaned_special = re.sub(r'(?<=E\d)O(?=\d)', '0', full_text)
    full_text = cleaned_special.replace("E4O7A", "E407A")

    pattern = re.compile(r'E\s*(\d+)([A-Z]?)')
    
    matches = pattern.findall(full_text)
    
    found_clean_codes = []
    for match in matches:
        # Може да има празно място между цифрите и буквата, оправяме го
        clean_code = "E" + match[0] + match[1]
        # За случай като "E05" -> "E05" (махаме водещите нули за чиста проверка)
        # found_clean_codes.append(re.sub(r'E0*', 'E', clean_code))
        found_clean_codes.append(clean_code)

    return found_clean_codes

# Интерфейс
st.title("🛡️ Прецизен скенер за Е-номера")
st.write("Качете снимка на етикета. Този модел е обучен да засича Е120, E407a и други с грешки.")

uploaded_file = st.file_uploader("Изберете снимка на етикета...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    with st.spinner('Анализирам текста...'):
        img_array = np.array(image)
        # Четем текста с малко по-ниски нива на детайлност, за да хванем по-големи блокове
        results = reader.readtext(img_array, detail=0)
        
        # Разпознаваме всички Е-номера
        detected_e_codes = extract_and_clean_e_numbers(results)
        
        # Показаване на разпознатия текст за дебъгване
        st.subheader("Извлечени сурови данни:")
        with st.expander("Виж извлечените текстови блокове"):
            st.write(results)

        st.subheader("Засечени потенциални Е-номера (след почистване):")
        st.write(detected_e_codes if detected_e_codes else "Няма открити Е-номера.")

        # Проверка срещу базата данни
        found_bad_stuff = []
        # Важно: премахваме дубликатите и водещите нули при проверката, за да е точна
        unique_codes = sorted(set(detected_e_codes))
        
        for code in unique_codes:
            # Премахваме водещите нули само за проверката в базата (напр. Е005 -> E5)
            # code_check = re.sub(r'E0+', 'E', code)
            
            # Търсим точен съвпадение (ключа в базата трябва да е без водещи нули, освен за Е0х)
            if code in INGREDIENT_DATABASE:
                found_bad_stuff.append((code, INGREDIENT_DATABASE[code]))

        st.divider()
        if found_bad_stuff:
            st.warning("⚠️ Внимание! В етикета са открити следните добавки:")
            # Ползваме unique_codes за заглавията, за да е точно засичането от снимката
            for code, description in sorted(found_bad_stuff):
                st.write(f"- **{code}:** {description}")
        elif detected_e_codes:
            st.success(f"✅ Засечени са Е-номера, но никой от тях не е в нашия списък с вредни добавки.")
        else:
            st.success("✅ Не бяха открити никакви Е-номера на снимката.")
