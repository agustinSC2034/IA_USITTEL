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
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

def crear_prompt_router(pregunta: str, dataframes: Dict[str, pd.DataFrame], contexto: list = None) -> str:
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
    
    # Agregar contexto si existe
    contexto_texto = ""
    if contexto and len(contexto) > 0:
        contexto_texto = "\n\nCONTEXTO DE LA CONVERSACIÓN ANTERIOR:\n"
        for item in contexto[-3:]:  # Últimas 3 interacciones
            contexto_texto += f"- Usuario: {item['pregunta']}\n"
            contexto_texto += f"  Búsqueda en: {item.get('dataframe', 'N/A')}\n"
            if 'filtros' in item:
                contexto_texto += f"  Filtros usados: {item['filtros']}\n"

    
    prompt = f"""Eres un experto en análisis de datos para un ISP llamado USITTEL.

PREGUNTA DEL USUARIO:
{pregunta}{contexto_texto}

FUENTES DE DATOS DISPONIBLES:
{descripcion_fuentes}

TAREA:
Analiza la pregunta y determina:
1. En qué fuente de datos (DataFrame) buscar
2. Qué filtros aplicar para responder la pregunta con precisión.

IMPORTANTE:
- Puedes aplicar MÚLTIPLES filtros si es necesario (ej: categoría Y estado).
- "Abierto" y "Pendiente" son sinónimos. Ambos significan tickets NO finalizados.
- Si el usuario pide tickets "abiertos" o "pendientes", debes filtrar para EXCLUIR "Resuelto" y "Cerrado".
- Usa el operador "!=" para excluir valores.

EJEMPLOS:
- "¿Cuántos clientes hay?" → {{"dataframe": "clientes_datos", "filtros": []}}
- "¿Cuál es el estado de Juan Perez?" → {{"dataframe": "clientes_datos", "filtros": [{{"columna": "Nombre", "valor": "Juan Perez"}}]}}
- "¿Tickets de nueva instalación pendientes?" → {{"dataframe": "tickets", "filtros": [{{"columna": "Categoría Ticket", "valor": "Nueva Instalación"}}, {{"columna": "Estado del Ticket", "valor": "Resuelto", "operador": "!="}}, {{"columna": "Estado del Ticket", "valor": "Cerrado", "operador": "!="}}]}}
- "¿NAPs con 0 puertos libres?" → {{"dataframe": "naps", "filtros": [{{"columna": "Puertos Libres", "valor": "0"}}]}}

RESPONDE ÚNICAMENTE con un JSON válido en este formato:
{{
    "dataframe": "nombre_del_dataframe",
    "filtros": [
        {{
            "columna": "nombre_columna",
            "valor": "valor_a_buscar",
            "operador": "==" (default) o "!=" o ">" o "<" o "contiene"
        }}
    ],
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
        # Usar gemini-3-flash-preview (recién habilitado)
        model = genai.GenerativeModel('gemini-3-flash-preview')
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

def buscar_en_dataframe(df: pd.DataFrame, filtros: List[Dict]) -> pd.DataFrame:
    """
    Realiza una búsqueda en un DataFrame aplicando múltiples filtros.
    
    Args:
        df: DataFrame donde buscar
        filtros: Lista de diccionarios con {'columna', 'valor', 'operador'}
    
    Returns:
        DataFrame filtrado
    """
    try:
        if not filtros:
            return df
            
        df_filtrado = df.copy()
        
        for filtro in filtros:
            columna = filtro.get('columna')
            valor = filtro.get('valor')
            operador = filtro.get('operador', 'contiene') # Default a contiene
            
            if not columna:
                # Búsqueda global si no hay columna (solo si hay valor)
                if valor:
                    mascara_global = pd.Series([False] * len(df_filtrado), index=df_filtrado.index)
                    for col in df_filtrado.columns:
                        if df_filtrado[col].dtype == 'object':
                            mascara_global |= df_filtrado[col].astype(str).str.contains(str(valor), case=False, na=False)
                    df_filtrado = df_filtrado[mascara_global]
                continue

            # Verificar columna
            if columna not in df_filtrado.columns:
                columnas_lower = {col.lower(): col for col in df_filtrado.columns}
                if columna.lower() in columnas_lower:
                    columna = columnas_lower[columna.lower()]
                else:
                    st.warning(f"⚠️ Columna '{columna}' no encontrada. Ignorando filtro.")
                    continue
            
            # Aplicar filtro según operador
            if operador == '!=':
                if df_filtrado[columna].dtype == 'object':
                    df_filtrado = df_filtrado[~df_filtrado[columna].astype(str).str.contains(str(valor), case=False, na=False)]
                else:
                    try:
                        v_num = float(valor)
                        df_filtrado = df_filtrado[df_filtrado[columna] != v_num]
                    except:
                        df_filtrado = df_filtrado[df_filtrado[columna].astype(str) != str(valor)]
            
            elif operador == '>':
                try:
                    v_num = float(valor)
                    df_filtrado = df_filtrado[df_filtrado[columna] > v_num]
                except:
                    pass # Ignorar si no es numérico
            
            elif operador == '<':
                try:
                    v_num = float(valor)
                    df_filtrado = df_filtrado[df_filtrado[columna] < v_num]
                except:
                    pass

            elif operador == '==':
                 if df_filtrado[columna].dtype == 'object':
                    # Búsqueda exacta para strings (case insensitive)
                    df_filtrado = df_filtrado[df_filtrado[columna].astype(str).str.lower() == str(valor).lower()]
                 else:
                    try:
                        v_num = float(valor)
                        df_filtrado = df_filtrado[df_filtrado[columna] == v_num]
                    except:
                        df_filtrado = df_filtrado[df_filtrado[columna].astype(str) == str(valor)]

            else: # 'contiene' o default
                # Lógica original de "contiene" y soporte para múltiples valores con "o"
                import re
                valores_multiples = re.split(r'\s+y\s+|\s+o\s+|,\s*', str(valor))
                
                mascara_filtro = pd.Series([False] * len(df_filtrado), index=df_filtrado.index)
                
                if len(valores_multiples) > 1:
                    for v in valores_multiples:
                        v = v.strip()
                        if df_filtrado[columna].dtype == 'object':
                            mascara_filtro |= df_filtrado[columna].astype(str).str.contains(str(v), case=False, na=False)
                        else:
                            try:
                                v_num = float(v) if '.' in v else int(v)
                                mascara_filtro |= (df_filtrado[columna] == v_num)
                            except:
                                mascara_filtro |= (df_filtrado[columna].astype(str) == str(v))
                else:
                    if df_filtrado[columna].dtype == 'object':
                        mascara_filtro = df_filtrado[columna].astype(str).str.contains(str(valor), case=False, na=False)
                    else:
                        try:
                            v_num = float(valor)
                            mascara_filtro = (df_filtrado[columna] == v_num)
                        except:
                            mascara_filtro = (df_filtrado[columna].astype(str) == str(valor))
                
                df_filtrado = df_filtrado[mascara_filtro]

        return df_filtrado

    except Exception as e:
        st.error(f"❌ Error en búsqueda: {str(e)}")
        return pd.DataFrame()

# ==================== SINTETIZADOR ====================

def crear_prompt_sintetizador(pregunta: str, resultados: pd.DataFrame, dataframe_nombre: str, parametros_busqueda: dict = None) -> str:
    """
    Crea el prompt para que la IA sintetice la respuesta final.
    
    Args:
        pregunta: Pregunta original del usuario
        resultados: DataFrame con los resultados encontrados
        dataframe_nombre: Nombre de la fuente de datos
        parametros_busqueda: Parámetros usados en la búsqueda
    
    Returns:
        Prompt formateado
    """
    if resultados.empty:
        prompt = f"""La búsqueda en '{dataframe_nombre}' no arrojó resultados para: "{pregunta}"

Responde de forma amable y concisa indicando que no se encontró información."""
    else:
        total_registros = len(resultados)
        
        # Generar estadísticas útiles según la pregunta
        info_estadisticas = ""
        if 'Puertos Libres' in resultados.columns:
            conteo_puertos = resultados['Puertos Libres'].value_counts().sort_index()
            info_estadisticas = "\n\nESTADÍSTICAS DE PUERTOS LIBRES:\n"
            for puertos, cantidad in conteo_puertos.items():
                info_estadisticas += f"- {cantidad} NAPs con {puertos} puertos libres\n"
        
        # Mostrar muestra de datos (máximo 5 para el prompt)
        if total_registros > 5:
            muestra = resultados.head(5).to_string(index=False)
            ejemplos = f"\n\nEJEMPLOS (5 de {total_registros}):\n{muestra}"
        else:
            muestra = resultados.to_string(index=False)
            ejemplos = f"\n\nTODOS LOS REGISTROS ({total_registros}):\n{muestra}"
        
        prompt = f"""Eres un asistente directo y conversacional estilo ChatGPT.

PREGUNTA: {pregunta}

RESULTADOS: {total_registros} registros en '{dataframe_nombre}'
{info_estadisticas}{ejemplos}

RESPONDE:
- Directo, sin saludos ni despedidas formales
- Números exactos cuando preguntan "cuántos": {total_registros}
- Si hay múltiples valores filtrados, explica cada uno
- Tono ChatGPT: natural, claro, sin ceremonias
- Máximo 2-3 oraciones breves
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
    with st.status("🤔 Analizando tu pregunta...", expanded=False) as status:
        st.write("1️⃣ Determinando dónde buscar...")
        
        # Obtener contexto de conversación
        contexto = st.session_state.get('contexto_conversacion', [])
        
        prompt_router = crear_prompt_router(pregunta, dataframes, contexto)
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
        
        filtros = parametros.get('filtros', [])
        # Retrocompatibilidad por si acaso la IA alucina el formato viejo
        if not filtros and 'columna' in parametros:
             filtros = [{'columna': parametros['columna'], 'valor': parametros['valor']}]
        
        if filtros:
            for i, f in enumerate(filtros):
                op = f.get('operador', 'contiene')
                col = f.get('columna', 'Global')
                val = f.get('valor', '')
                st.write(f"🔹 Filtro {i+1}: **{col}** {op} **{val}**")
        else:
            st.write("🔹 Sin filtros específicos (búsqueda general)")
        
        # PASO 2: Motor de Búsqueda - Ejecutar consulta
        st.write("2️⃣ Buscando en los datos...")
        
        if parametros['dataframe'] not in dataframes:
            status.update(label="❌ Fuente de datos no disponible", state="error")
            return f"La fuente de datos '{parametros['dataframe']}' no está disponible.", None
        
        df = dataframes[parametros['dataframe']]
        resultados = buscar_en_dataframe(df, filtros)
        
        st.write(f"📦 Encontrados: **{len(resultados)}** registros")
        
        # PASO 3: Sintetizador - Generar respuesta
        st.write("3️⃣ Generando respuesta...")
        prompt_sintetizador = crear_prompt_sintetizador(pregunta, resultados, parametros['dataframe'])
        respuesta_final = llamar_gemini(prompt_sintetizador, temperatura=0.3)
        
        # Guardar en contexto para próximas preguntas
        st.session_state.contexto_conversacion.append({
            'pregunta': pregunta,
            'dataframe': parametros['dataframe'],
            'filtros': filtros
        })
        
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
    
    # Inicializar historial de chat y contexto
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    
    if "contexto_conversacion" not in st.session_state:
        st.session_state.contexto_conversacion = []
    
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
