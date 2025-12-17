"""
Chatbot Interno USITTEL - RAG con Google Sheets y Gemini
Desarrollado para consultas deterministas sobre clientes, NAPs, tickets, etc.
"""

import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
from datetime import datetime
from typing import Dict, Optional, List

# ==================== CONFIGURACIÓN ====================

# Configurar la API key de Gemini
# Intenta primero desde variables de entorno (.env), luego desde secrets.toml
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except:
        GEMINI_API_KEY = ""

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# URLs de Google Sheets (convertidas a formato CSV exportable)
SHEETS_URLS = {
    "naps": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=443573341",
    "clientes_naps": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=443573341",
    "clientes_cuentas": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=101720087",
    "clientes_datos": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=1694258191",
    "tickets": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=0",
    "clientes_olts": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=819538991",
    "dashboards": "https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/export?format=csv&gid=44575307"
}

# ==================== FUNCIONES DE CARGA DE DATOS ====================

@st.cache_data(ttl=60)  # Cache de 60 segundos para datos frescos
def cargar_google_sheet(url: str, nombre: str) -> Optional[pd.DataFrame]:
    """
    Carga una Google Sheet como DataFrame de Pandas.
    
    Args:
        url: URL de exportación CSV de Google Sheets
        nombre: Nombre descriptivo de la hoja (para logs)
    
    Returns:
        DataFrame con los datos o None si falla
    """
    try:
        df = pd.read_csv(url)
        st.sidebar.success(f"✅ {nombre}: {len(df)} filas cargadas")
        return df
    except Exception as e:
        st.sidebar.error(f"❌ Error en {nombre}: {str(e)}")
        return None

@st.cache_data(ttl=60)
def cargar_todos_los_datos() -> Dict[str, pd.DataFrame]:
    """
    Carga todas las hojas de Google Sheets.
    
    Returns:
        Diccionario con nombre_hoja: DataFrame
    """
    dataframes = {}
    
    with st.spinner("🔄 Cargando datos de Google Sheets..."):
        for nombre, url in SHEETS_URLS.items():
            df = cargar_google_sheet(url, nombre)
            if df is not None:
                dataframes[nombre] = df
    
    return dataframes

# ==================== FUNCIONES DE IA ====================

def crear_prompt_router(pregunta: str, dataframes: Dict[str, pd.DataFrame]) -> str:
    """
    Crea el prompt para que la IA decida dónde buscar.
    
    Args:
        pregunta: Pregunta del usuario
        dataframes: Diccionario de DataFrames disponibles
    
    Returns:
        Prompt formateado para el modelo
    """
    # Crear descripción de las fuentes de datos disponibles
    descripcion_fuentes = ""
    for nombre, df in dataframes.items():
        columnas = ", ".join(df.columns.tolist()[:10])  # Primeras 10 columnas
        total_filas = len(df)
        descripcion_fuentes += f"\n- **{nombre}** ({total_filas} registros): {columnas}"
    
    prompt = f"""Eres un experto en análisis de datos para un ISP llamado USITTEL.

PREGUNTA DEL USUARIO:
{pregunta}

FUENTES DE DATOS DISPONIBLES:
{descripcion_fuentes}

TAREA:
Analiza la pregunta y determina:
1. En qué fuente de datos (DataFrame) buscar
2. Qué columna filtrar (puede ser vacío si es una pregunta general)
3. Qué valor buscar (puede ser vacío si es un conteo o pregunta general)

EJEMPLOS:
- "¿Cuántos clientes hay?" → {{"dataframe": "clientes_datos", "columna": "", "valor": ""}}
- "¿Cuántas NAPs hay?" → {{"dataframe": "naps", "columna": "", "valor": ""}}
- "¿Cuál es el estado de Juan Perez?" → {{"dataframe": "clientes_datos", "columna": "Nombre", "valor": "Juan Perez"}}

RESPONDE ÚNICAMENTE con un JSON válido en este formato:
{{
    "dataframe": "nombre_del_dataframe",
    "columna": "nombre_de_columna_o_vacio",
    "valor": "valor_a_buscar_o_vacio",
    "explicacion": "breve explicación"
}}

Si no puedes determinar dónde buscar, responde:
{{
    "error": "No puedo determinar dónde buscar esta información"
}}
"""
    return prompt

def llamar_gemini(prompt: str, temperatura: float = 0.1) -> str:
    """
    Llama a la API de Gemini y retorna la respuesta.
    
    Args:
        prompt: Texto del prompt
        temperatura: Nivel de creatividad (0 = determinista, 1 = creativo)
    
    Returns:
        Respuesta del modelo
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperatura,
            )
        )
        return response.text
    except Exception as e:
        return f"Error al llamar a Gemini: {str(e)}"

def extraer_json_de_respuesta(texto: str) -> Optional[dict]:
    """
    Extrae un JSON de la respuesta del modelo.
    
    Args:
        texto: Texto que puede contener JSON
    
    Returns:
        Diccionario con el JSON parseado o None
    """
    try:
        # Intentar parsear directamente
        return json.loads(texto)
    except:
        # Buscar JSON entre marcadores de código
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', texto, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Buscar cualquier objeto JSON en el texto
        json_match = re.search(r'\{.*\}', texto, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
    
    return None

# ==================== MOTOR DE BÚSQUEDA ====================

def buscar_en_dataframe(df: pd.DataFrame, columna: str, valor: str) -> pd.DataFrame:
    """
    Realiza una búsqueda exacta en un DataFrame.
    
    Args:
        df: DataFrame donde buscar
        columna: Nombre de la columna (puede estar vacío para búsquedas generales)
        valor: Valor a buscar (puede estar vacío para retornar todo)
    
    Returns:
        DataFrame filtrado con los resultados
    """
    try:
        # Si no hay columna ni valor, retornar todo el DataFrame
        if not columna and not valor:
            return df
        
        # Si no hay columna pero hay valor, buscar en todas las columnas de texto
        if not columna and valor:
            mascara_global = pd.Series([False] * len(df))
            for col in df.columns:
                if df[col].dtype == 'object':
                    mascara_global |= df[col].astype(str).str.contains(str(valor), case=False, na=False)
            return df[mascara_global]
        
        # Verificar que la columna existe
        if columna not in df.columns:
            # Intentar búsqueda case-insensitive en nombres de columnas
            columnas_lower = {col.lower(): col for col in df.columns}
            if columna.lower() in columnas_lower:
                columna = columnas_lower[columna.lower()]
            else:
                st.warning(f"⚠️ Columna '{columna}' no encontrada. Columnas disponibles: {', '.join(df.columns.tolist()[:5])}")
                return pd.DataFrame()
        
        # Si hay columna pero no valor, retornar todo
        if columna and not valor:
            return df
        
        # Realizar búsqueda (case-insensitive si es texto)
        if df[columna].dtype == 'object':
            mascara = df[columna].astype(str).str.contains(str(valor), case=False, na=False)
        else:
            mascara = df[columna] == valor
        
        return df[mascara]
    
    except Exception as e:
        st.error(f"❌ Error en búsqueda: {str(e)}")
        return pd.DataFrame()

# ==================== SINTETIZADOR ====================

def crear_prompt_sintetizador(pregunta: str, resultados: pd.DataFrame, dataframe_nombre: str) -> str:
    """
    Crea el prompt para que la IA sintetice la respuesta final.
    
    Args:
        pregunta: Pregunta original del usuario
        resultados: DataFrame con los resultados encontrados
        dataframe_nombre: Nombre de la fuente de datos
    
    Returns:
        Prompt formateado
    """
    if resultados.empty:
        prompt = f"""La búsqueda en '{dataframe_nombre}' no arrojó resultados para: "{pregunta}"

Responde de forma amable indicando que no se encontró información y sugiere reformular la pregunta."""
    else:
        # Para conteos o preguntas generales, mostrar estadísticas
        total_registros = len(resultados)
        
        # Si hay muchos registros, mostrar solo los primeros
        if total_registros > 10:
            resultados_texto = resultados.head(10).to_string(index=False)
            nota_adicional = f"\n\n(Se muestran solo los primeros 10 de {total_registros} registros encontrados)"
        else:
            resultados_texto = resultados.to_string(index=False)
            nota_adicional = ""
        
        prompt = f"""Eres un asistente virtual de USITTEL. Un usuario preguntó:

PREGUNTA: {pregunta}

DATOS ENCONTRADOS en '{dataframe_nombre}' (Total: {total_registros} registros):
{resultados_texto}{nota_adicional}

TAREA:
Responde la pregunta del usuario de forma clara, profesional y amable, usando ÚNICAMENTE la información proporcionada.
- Si pregunta "cuántos", responde con el número exacto: {total_registros}
- Si hay detalles específicos, menciónalos
- No inventes ni agregues datos que no estén en la tabla
- Si hay muchos resultados, puedes resumir las estadísticas principales
"""
    
    return prompt

# ==================== PIPELINE COMPLETO RAG ====================

def procesar_pregunta(pregunta: str, dataframes: Dict[str, pd.DataFrame]) -> tuple[str, Optional[pd.DataFrame]]:
    """
    Pipeline completo de RAG (Retrieval Augmented Generation).
    
    Args:
        pregunta: Pregunta del usuario
        dataframes: Diccionario con todas las fuentes de datos
    
    Returns:
        Tupla (respuesta_texto, dataframe_encontrado)
    """
    # PASO 1: Router - Decidir dónde buscar
    with st.status("🤔 Analizando tu pregunta...", expanded=True) as status:
        st.write("1️⃣ Determinando dónde buscar...")
        prompt_router = crear_prompt_router(pregunta, dataframes)
        respuesta_router = llamar_gemini(prompt_router, temperatura=0.1)
        
        parametros = extraer_json_de_respuesta(respuesta_router)
        
        if not parametros:
            status.update(label="❌ No pude entender la pregunta", state="error")
            return "Lo siento, no pude interpretar tu pregunta. ¿Podrías reformularla?", None
        
        if "error" in parametros:
            status.update(label="❌ No encontré dónde buscar", state="error")
            return parametros["error"], None
        
        # Mostrar decisión del router
        st.write(f"✅ Buscaré en: **{parametros['dataframe']}**")
        st.write(f"📊 Columna: **{parametros['columna']}**")
        st.write(f"🔍 Valor: **{parametros['valor']}**")
        
        # PASO 2: Motor de Búsqueda - Ejecutar consulta
        st.write("2️⃣ Buscando en los datos...")
        
        if parametros['dataframe'] not in dataframes:
            status.update(label="❌ Fuente de datos no disponible", state="error")
            return f"La fuente de datos '{parametros['dataframe']}' no está disponible.", None
        
        df = dataframes[parametros['dataframe']]
        resultados = buscar_en_dataframe(df, parametros['columna'], parametros['valor'])
        
        st.write(f"📦 Encontrados: **{len(resultados)}** registros")
        
        # PASO 3: Sintetizador - Generar respuesta
        st.write("3️⃣ Generando respuesta...")
        prompt_sintetizador = crear_prompt_sintetizador(pregunta, resultados, parametros['dataframe'])
        respuesta_final = llamar_gemini(prompt_sintetizador, temperatura=0.3)
        
        status.update(label="✅ ¡Listo!", state="complete")
    
    return respuesta_final, resultados

# ==================== INTERFAZ DE STREAMLIT ====================

def main():
    """Función principal de la aplicación."""
    
    # Configuración de la página
    st.set_page_config(
        page_title="Chatbot USITTEL",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Título
    st.title("🤖 Chatbot Interno USITTEL")
    st.markdown("*Asistente inteligente para consultas sobre clientes, NAPs, tickets y más*")
    
    # Sidebar con información
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Verificar API Key
        if not GEMINI_API_KEY:
            st.error("❌ API Key de Gemini no configurada")
            st.info("Configura la variable de entorno GEMINI_API_KEY o agrégala en .streamlit/secrets.toml")
            st.stop()
        else:
            st.success("✅ API Key configurada")
        
        st.divider()
        st.header("📊 Estado de Datos")
        
        # Botón para recargar datos
        if st.button("🔄 Recargar datos"):
            st.cache_data.clear()
            st.rerun()
    
    # Cargar datos
    dataframes = cargar_todos_los_datos()
    
    if not dataframes:
        st.error("❌ No se pudieron cargar los datos. Verifica las URLs de Google Sheets.")
        st.stop()
    
    st.sidebar.info(f"📦 {len(dataframes)} fuentes de datos activas")
    
    # Inicializar historial de chat
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    
    # Mostrar historial de chat
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])
            if mensaje.get("dataframe") is not None and not mensaje["dataframe"].empty:
                with st.expander("📊 Ver datos encontrados"):
                    st.dataframe(mensaje["dataframe"], use_container_width=True)
    
    # Input del usuario
    if pregunta := st.chat_input("Escribe tu pregunta aquí..."):
        # Agregar pregunta al historial
        st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
        
        # Mostrar pregunta
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        # Procesar y responder
        with st.chat_message("assistant"):
            respuesta, datos_encontrados = procesar_pregunta(pregunta, dataframes)
            st.markdown(respuesta)
            
            # Mostrar datos encontrados si existen
            if datos_encontrados is not None and not datos_encontrados.empty:
                with st.expander("📊 Ver datos encontrados"):
                    st.dataframe(datos_encontrados, use_container_width=True)
        
        # Agregar respuesta al historial
        st.session_state.mensajes.append({
            "rol": "assistant",
            "contenido": respuesta,
            "dataframe": datos_encontrados
        })
    
    # Footer
    st.divider()
    st.caption(f"🕐 Última actualización de datos: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("💡 Tip: Los datos se actualizan automáticamente cada 60 segundos")

if __name__ == "__main__":
    main()
