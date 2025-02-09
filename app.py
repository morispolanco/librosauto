import streamlit as st
import requests
from docx import Document
from io import BytesIO
import re

# Función para limpiar Markdown
def clean_markdown(text):
    """Elimina marcas de Markdown del texto."""
    text = re.sub(r'[#*_`]', '', text)  # Eliminar caracteres especiales de Markdown
    return text.strip()

# Función para generar un capítulo
def generate_chapter(api_key, topic, audience, chapter_number):
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "Eres un asistente útil que escribe en español."},
            {"role": "user", "content": f"Escribe el capítulo {chapter_number} de un libro sobre {topic} dirigido a {audience} con 2000-2500 palabras en español."}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Lanza una excepción si hay un error HTTP
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error en la generación del capítulo.")
    except Exception as e:
        st.error(f"Error al generar el capítulo {chapter_number}: {str(e)}")
        content = "Error en la generación del capítulo."
    return clean_markdown(content)

# Función para crear un documento Word
def create_word_document(chapters, title):
    doc = Document()
    doc.add_heading(title, level=1)
    for i, chapter in enumerate(chapters, 1):
        doc.add_heading(f"Capítulo {i}", level=2)
        doc.add_paragraph(chapter)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Configuración de Streamlit
st.title("Generador de Libros Automático 📚")

# Validación de claves secretas
if "DASHSCOPE_API_KEY" not in st.secrets:
    st.error("Por favor, configura la clave API en los secretos de Streamlit.")
    st.stop()

api_key = st.secrets["DASHSCOPE_API_KEY"]

# Entradas del usuario
topic = st.text_input("Introduce el tema del libro:")
audience = st.text_input("¿A quién va dirigido el libro?")
num_chapters = st.slider("Número de capítulos", min_value=1, max_value=20, value=5)

# Validación de entradas
if st.button("Generar Libro"):
    if not topic or not audience:
        st.error("Por favor, introduce un tema y una audiencia válidos.")
        st.stop()

    chapters = []
    progress_bar = st.progress(0)
    for i in range(1, num_chapters + 1):
        st.write(f"Generando capítulo {i}...")
        chapter_content = generate_chapter(api_key, topic, audience, i)
        
        # Verificar longitud del capítulo
        word_count = len(chapter_content.split())
        if word_count < 2000 or word_count > 2500:
            st.warning(f"El capítulo {i} tiene {word_count} palabras. No cumple con el rango esperado (2000-2500).")
        
        chapters.append(chapter_content)
        with st.expander(f"Capítulo {i}"):
            st.write(chapter_content)
        progress_bar.progress(i / num_chapters)
    
    # Crear y descargar el archivo Word
    word_file = create_word_document(chapters, topic)
    st.download_button(
        label="Descargar en Word",
        data=word_file,
        file_name=f"{topic}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# Pie de página mejorado
st.markdown("""
    <footer style='text-align: center; padding: 10px; background-color: #f8f9fa; border-top: 1px solid #ddd;'>
        <a href='https://hablemosbien.org' target='_blank' style='color: #007bff; text-decoration: none;'>Copyright Hablemos bien</a>
    </footer>
""", unsafe_allow_html=True)
