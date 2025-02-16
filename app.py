import streamlit as st
import requests
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO
import re

# Función para limpiar Markdown
def clean_markdown(text):
    """Elimina marcas de Markdown del texto."""
    text = re.sub(r'[#*_`]', '', text)  # Eliminar caracteres especiales de Markdown
    return text.strip()

# Función para aplicar reglas de capitalización según el idioma
def format_title(title, language):
    """
    Formatea el título según las reglas gramaticales del idioma.
    - Español: Solo mayúscula inicial en la primera palabra y nombres propios.
    - Otros idiomas: Mayúscula inicial en cada palabra.
    """
    if language.lower() == "spanish":
        words = title.split()
        formatted_words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        return " ".join(formatted_words)
    else:
        return title.title()

# Función para generar un capítulo con secciones
def generate_chapter(api_key, topic, audience, chapter_number, language, instructions=""):
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    message_content = f"Write chapter {chapter_number} of a book about {topic} aimed at {audience} with 2000-2500 words in {language}. Include 5 sections."
    
    if instructions:
        message_content += f" Additional instructions: {instructions}"
    
    data = {
        "model": "qwen-turbo",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant that writes in {language}."},
            {"role": "user", "content": message_content}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error generating the chapter.")
    except Exception as e:
        st.error(f"Error generating chapter {chapter_number}: {str(e)}")
        content = "Error generating the chapter."
    return clean_markdown(content)

# Función para agregar numeración de páginas al documento Word
def add_page_numbers(doc):
    for section in doc.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Center alignment
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar)
        run._r.append(instrText)
        run._r.append(fldChar2)

# Función para crear una tabla de contenido
def generate_table_of_contents(topic, num_chapters, include_intro, include_conclusion, language):
    toc = "Table of Contents:\n"
    if include_intro:
        toc += "Introduction\n"
    for i in range(1, num_chapters + 1):
        chapter_title = f"Chapter {i}" if language.lower() != "spanish" else f"Capítulo {i}"
        toc += f"{chapter_title}\n"
        for j in range(1, 6):  # Cinco secciones por capítulo
            section_title = f"Section {j}"
            toc += f"  {section_title}\n"
    if include_conclusion:
        toc += "Conclusions\n"
    return toc

# Función para crear un documento Word con formato específico
def create_word_document(chapters, title, author_name, author_bio, language, table_of_contents):
    doc = Document()

    # Configurar el tamaño de página (5.5 x 8.5 pulgadas)
    section = doc.sections[0]
    section.page_width = Inches(5.5)
    section.page_height = Inches(8.5)

    # Configurar márgenes de 0.8 pulgadas en todo
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    # Añadir título formateado según el idioma
    formatted_title = format_title(title, language)
    title_paragraph = doc.add_paragraph()
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_paragraph.add_run(formatted_title)
    title_run.bold = True
    title_run.font.size = Pt(14)
    title_run.font.name = "Times New Roman"

    # Añadir nombre del autor si está proporcionado
    if author_name:
        author_paragraph = doc.add_paragraph()
        author_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_run = author_paragraph.add_run(author_name)
        author_run.font.size = Pt(12)
        author_run.font.name = "Times New Roman"
        doc.add_page_break()

    # Añadir perfil del autor si está proporcionado
    if author_bio:
        bio_paragraph = doc.add_paragraph("Author Information")
        bio_paragraph.style = "Heading 2"
        bio_paragraph.runs[0].font.size = Pt(11)
        bio_paragraph.runs[0].font.name = "Times New Roman"
        doc.add_paragraph(author_bio).style = "Normal"
        doc.add_page_break()

    # Añadir tabla de contenido
    toc_paragraph = doc.add_paragraph("Table of Contents")
    toc_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    toc_paragraph.runs[0].bold = True
    toc_paragraph.runs[0].font.size = Pt(12)
    toc_paragraph.runs[0].font.name = "Times New Roman"
    doc.add_paragraph(table_of_contents).style = "Normal"
    doc.add_page_break()

    # Añadir capítulos
    for i, chapter in enumerate(chapters, 1):
        # Añadir encabezado del capítulo formateado según el idioma
        chapter_title_text = f"Chapter {i}" if language.lower() != "spanish" else f"Capítulo {i}"
        formatted_chapter_title = format_title(chapter_title_text, language)
        chapter_title = doc.add_paragraph(formatted_chapter_title)
        chapter_title.style = "Heading 1"
        chapter_title.runs[0].font.size = Pt(12)
        chapter_title.runs[0].font.name = "Times New Roman"

        # Dividir el contenido del capítulo en secciones
        sections = chapter.split("\n\n")  # Suponemos que las secciones están separadas por dos saltos de línea
        for j, section_text in enumerate(sections, 1):
            section_title = f"Section {j}"
            section_paragraph = doc.add_paragraph(section_title)
            section_paragraph.style = "Heading 2"
            section_paragraph.runs[0].font.size = Pt(11)
            section_paragraph.runs[0].font.name = "Times New Roman"

            # Añadir el contenido de la sección
            paragraph = doc.add_paragraph(section_text.strip())
            paragraph.style = "Normal"
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            paragraph.paragraph_format.space_after = Pt(0)
            for run in paragraph.runs:
                run.font.size = Pt(11)
                run.font.name = "Times New Roman"

        doc.add_page_break()

    # Agregar numeración de páginas
    add_page_numbers(doc)

    # Guardar el documento en memoria
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Configuración de Streamlit
st.set_page_config(
    page_title="Automatic Book Generator",
    page_icon="📚",
)

# Título con ícono
st.title("📚 Automatic Book Generator")

# Barra lateral con instrucciones y anuncio
st.sidebar.header("📖 How does this app work?")
st.sidebar.markdown("""
This application automatically generates non-fiction books in `.docx` format based on a topic and target audience.  
**Steps to use it:**
1. Enter the book's topic.
2. Specify the target audience.
3. Write special instructions (optional).
4. Select the number of chapters desired (maximum 20).
5. Choose the book's language.
6. Provide or generate a table of contents.
7. Click "Generate Book".
8. Download the generated file.
""")
st.sidebar.markdown("""
---
**📝 Text correction in 24 hours**  
👉 [Hablemos Bien](https://hablemosbien.org)
""")

# Validación de claves secretas
if "DASHSCOPE_API_KEY" not in st.secrets:
    st.error("Please configure the API key in Streamlit secrets.")
    st.stop()
api_key = st.secrets["DASHSCOPE_API_KEY"]

# Entradas del usuario
topic = st.text_input("📒 Book Topic:")
audience = st.text_input("🎯 Target Audience:")
instructions = st.text_area("📝 Special Instructions (optional):", 
                             placeholder="Example: Use a formal tone, include practical examples, avoid technical jargon...")
num_chapters = st.slider("🔢 Number of Chapters", min_value=1, max_value=20, value=5)

# Opciones para introducción y conclusiones
include_intro = st.checkbox("✅ Include Introduction", value=True)
include_conclusion = st.checkbox("✅ Include Conclusions", value=True)

# Menú desplegable para elegir el idioma
languages = [
    "English", "Spanish", "French", "German", "Chinese", "Japanese", 
    "Russian", "Portuguese", "Italian", "Arabic", "Medieval Latin", "Koine Greek"
]
selected_language = st.selectbox("🌐 Choose the book's language:", languages)

# Generación automática de la tabla de contenido
table_of_contents = generate_table_of_contents(topic, num_chapters, include_intro, include_conclusion, selected_language)
st.subheader("📋 Table of Contents")
st.text(table_of_contents)

# Botón para regenerar la tabla de contenido
if st.button("🔄 Regenerate Table of Contents"):
    table_of_contents = generate_table_of_contents(topic, num_chapters, include_intro, include_conclusion, selected_language)
    st.text(table_of_contents)

# Estado de Streamlit para almacenar los capítulos generados
if 'chapters' not in st.session_state:
    st.session_state.chapters = []

# Botón para generar el libro
if st.button("🚀 Generate Book"):
    if not topic or not audience:
        st.error("Please enter a valid topic and target audience.")
        st.stop()
    
    chapters = []
    progress_bar = st.progress(0)
    for i in range(1, num_chapters + 1):
        st.write(f"⏳ Generating chapter {i}...")
        chapter_content = generate_chapter(api_key, topic, audience, i, selected_language.lower(), instructions)
        chapters.append(chapter_content)
        progress_bar.progress(i / num_chapters)

    # Almacenar los capítulos en el estado de Streamlit
    st.session_state.chapters = chapters

# Mostrar opciones de descarga si hay capítulos generados
if st.session_state.chapters:
    st.subheader("⬇️ Download Options")
    word_file = create_word_document(st.session_state.chapters, topic, "", "", selected_language.lower(), table_of_contents)

    st.download_button(
        label="📥 Download in Word",
        data=word_file,
        file_name=f"{topic}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
