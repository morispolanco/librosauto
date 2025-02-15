import streamlit as st
import requests
from docx import Document
from io import BytesIO
import re
from ebooklib import epub

# Función para limpiar Markdown
def clean_markdown(text):
    """Elimina marcas de Markdown del texto."""
    text = re.sub(r'[#*_`]', '', text)  # Eliminar caracteres especiales de Markdown
    return text.strip()

# Función para generar un capítulo
def generate_chapter(api_key, topic, audience, chapter_number, instructions=""):
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Construir el mensaje con las instrucciones especiales
    message_content = f"Escribe el capítulo {chapter_number} de un libro sobre {topic} dirigido a {audience} con 2000-2500 palabras en español."
    if instructions:
        message_content += f" Instrucciones adicionales: {instructions}"
    
    data = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": "Eres un asistente útil que escribe en español."},
            {"role": "user", "content": message_content}
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

# Función para crear un archivo HTML
def create_html_document(chapters, title):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
            }}
            h1 {{
                color: #2c3e50;
            }}
            details {{
                margin-bottom: 20px;
            }}
            summary {{
                font-weight: bold;
                cursor: pointer;
                color: #34495e;
            }}
            p {{
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
    """
    for i, chapter in enumerate(chapters, 1):
        html_content += f"""
        <details>
            <summary>Capítulo {i}</summary>
            <p>{chapter}</p>
        </details>
        """
    html_content += """
    </body>
    </html>
    """
    return html_content.encode('utf-8')

# Función para crear un archivo eBook (.epub)
def create_epub_document(chapters, title):
    book = epub.EpubBook()

    # Metadatos del eBook
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('es')
    book.add_author('Generador Automático de Libros')

    # Crear capítulos
    epub_chapters = []
    for i, chapter in enumerate(chapters, 1):
        c = epub.EpubHtml(title=f'Capítulo {i}', file_name=f'chap_{i}.xhtml', lang='es')
        c.content = f"<h1>Capítulo {i}</h1><p>{chapter}</p>"
        book.add_item(c)
        epub_chapters.append(c)

    # Definir tabla de contenido
    book.toc = tuple(epub_chapters)

    # Agregar navegación
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Guardar el eBook en memoria
    buffer = BytesIO()
    epub.write_epub(buffer, book)
    buffer.seek(0)
    return buffer

# Configuración de Streamlit
st.set_page_config(
    page_title="Generador Automático de Libros",
    page_icon="📚",  # Ícono para la pestaña del navegador
)

# Título con ícono
st.title("📚 Generador automático de libros")

# Barra lateral con instrucciones y anuncio
st.sidebar.header("📖 ¿Cómo funciona esta app?")
st.sidebar.markdown("""
Esta aplicación genera automáticamente libros de no ficción en formato `.docx`, `HTML` o `eBook (.epub)` basados en un tema y una audiencia específica.  
**Pasos para usarla:**
1. Introduce el tema del libro.
2. Especifica a quién va dirigido.
3. Escribe instrucciones especiales (opcional).
4. Selecciona el número de capítulos deseados.
5. Haz clic en "Generar Libro".
6. Descarga el archivo generado.
""")
st.sidebar.markdown("""
---
**📝 Corrección de textos en 24 horas**  
👉 [Hablemos Bien](https://hablemosbien.org)
""")

# Validación de claves secretas
if "DASHSCOPE_API_KEY" not in st.secrets:
    st.error("Por favor, configura la clave API en los secretos de Streamlit.")
    st.stop()
api_key = st.secrets["DASHSCOPE_API_KEY"]

# Entradas del usuario
topic = st.text_input("📒 Tema del libro:")
audience = st.text_input("🎯 Audiencia objetivo:")
instructions = st.text_area("📝 Instrucciones especiales (opcional):", 
                             placeholder="Ejemplo: Usa un tono formal, incluye ejemplos prácticos, evita tecnicismos...")
num_chapters = st.slider("🔢 Número de capítulos", min_value=1, max_value=15, value=5)

# Estado de Streamlit para almacenar los capítulos generados
if 'chapters' not in st.session_state:
    st.session_state.chapters = []

# Botón para generar el libro
if st.button("🚀 Generar Libro"):
    if not topic or not audience:
        st.error("Por favor, introduce un tema y una audiencia válidos.")
        st.stop()
    
    chapters = []
    progress_bar = st.progress(0)
    for i in range(1, num_chapters + 1):
        st.write(f"⏳ Generando capítulo {i}...")
        chapter_content = generate_chapter(api_key, topic, audience, i, instructions)
        word_count = len(chapter_content.split())  # Contar palabras
        chapters.append(chapter_content)
        with st.expander(f" Capítulo {i} ({word_count} palabras)"):
            st.write(chapter_content)
        progress_bar.progress(i / num_chapters)
    
    # Almacenar los capítulos en el estado de Streamlit
    st.session_state.chapters = chapters

# Mostrar opciones de descarga si hay capítulos generados
if st.session_state.chapters:
    st.subheader("⬇️ Opciones de descarga")
    word_file = create_word_document(st.session_state.chapters, topic)
    html_file = create_html_document(st.session_state.chapters, topic)
    epub_file = create_epub_document(st.session_state.chapters, topic)

    st.download_button(
        label="📥 Descargar en Word",
        data=word_file,
        file_name=f"{topic}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    st.download_button(
        label="🌐 Descargar en HTML",
        data=html_file,
        file_name=f"{topic}.html",
        mime="text/html"
    )

    st.download_button(
        label="📖 Descargar en eBook (.epub)",
        data=epub_file,
        file_name=f"{topic}.epub",
        mime="application/epub+zip"
    )

# Pie de página simplificado
st.markdown("""
    <footer style='text-align: center; padding: 10px; background-color: #f8f9fa; border-top: 1px solid #ddd;'>
        <a href='https://hablemosbien.org' target='_blank' style='color: #007bff; text-decoration: none;'>Hablemos Bien</a>
    </footer>
""", unsafe_allow_html=True)
