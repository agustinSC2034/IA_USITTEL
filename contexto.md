Actúa como un Desarrollador Senior de Python Full-Stack experto en LLMs y Data Engineering.
Necesito desarrollar una aplicación web interna (Chatbot) para un ISP llamado USITTEL usando Streamlit.

CONTEXTO DEL PROBLEMA:
Actualmente usamos asistentes tipo GPTs/Gems conectados a Google Sheets, pero alucinan datos o no leen las actualizaciones recientes. Necesitamos una solución "determinista" donde la IA no adivine datos, sino que ejecute búsquedas exactas en DataFrames de Pandas.

OBJETIVO:
Crear un script en Python (app.py) usando Streamlit, Pandas y la API de OpenAI (modelo gpt-4o-mini) o Google Gemini (gemini-1.5-flash).
La aplicación debe leer varias hojas de cálculo de Google Sheets en tiempo real y responder preguntas operativas sobre clientes, NAPs, Tickets, etc.

ARQUITECTURA REQUERIDA (RAG Funcional):
No quiero que le pases el CSV entero al prompt de la IA. Quiero la siguiente lógica:
1. Input del usuario: "¿Cuál es el estado del cliente Juan Perez?"
2. Router (IA): Analiza la pregunta y decide:
   - En qué DataFrame buscar (ej: df_clientes).
   - Qué columna filtrar (ej: 'Nombre').
   - Qué valor buscar (ej: 'Juan Perez').
   - Retorna un JSON con estos parámetros.
3. Motor de Búsqueda (Python/Pandas): Ejecuta el filtro exacto: `df[df['Nombre'].str.contains('Juan Perez')]`.
4. Sintetizador (IA): Recibe SOLAMENTE las filas encontradas y redacta la respuesta final al usuario. Si el DataFrame vuelve vacío, la respuesta es "No se encontró información".

FUENTES DE DATOS (Google Sheets):
Las hojas se actualizan constantemente. Debes usar una función de carga con caché de corta duración (st.cache_data con ttl=60 segundos) para asegurar datos frescos.
Convierte las URLs de 'edit' a formato de exportación CSV para lectura con Pandas si es necesario, o usa la lógica adecuada.

URLs de las hojas:
1. NAPS (Cajas): https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=443573341
2. Clientes_naps: https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=443573341
3. Clientes_cuentas (Facturación): https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=101720087
4. Clientes_datos (Datos personales): https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=1694258191
5. Tickets (Soporte): https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=0
6. Clientes_OLTs: https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=819538991
7. Dashboards: https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/edit?gid=44575307

REQUISITOS TÉCNICOS:
- Lenguaje: Python 3.9+
- Librerías: streamlit, pandas, openai (o google-generativeai).
- Manejo de errores: Si una hoja falla al cargar, la app no debe romperse, debe avisar.
- Interfaz: Simple, con un chat input y visualización clara de los datos encontrados.
- Configuración: Usa st.secrets o variables de entorno para la API Key.

Por favor, escribe el código completo de `app.py` y genera un `requirements.txt`.