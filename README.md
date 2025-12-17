# 🤖 Chatbot Interno USITTEL

Chatbot inteligente para consultas sobre clientes, NAPs, tickets y facturación usando Google Sheets y Gemini AI.

## 🎯 Características

- ✅ **Sin alucinaciones**: Búsqueda determinista en datos reales
- 🔄 **Datos en tiempo real**: Actualización automática cada 60 segundos
- 🎨 **Interfaz simple**: Chat conversacional con Streamlit
- 💰 **Gratis**: Usa Gemini 1.5 Flash (cuota gratuita generosa)
- 📊 **Múltiples fuentes**: Consulta varias hojas de Google Sheets

## 📋 Requisitos Previos

1. **Python 3.9 o superior**
2. **Cuenta de Google** (para obtener API Key de Gemini)

## 🚀 Instalación

### Paso 1: Clonar o descargar este proyecto

Ya tienes los archivos en:
```
c:\Users\Aguus\OneDrive\Escritorio\IA_USITTEL\
```

### Paso 2: Instalar Python (si no lo tienes)

1. Ve a [python.org](https://www.python.org/downloads/)
2. Descarga Python 3.9 o superior
3. Durante la instalación, marca ✅ "Add Python to PATH"

### Paso 3: Instalar dependencias

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
pip install -r requirements.txt
```

### Paso 4: Obtener API Key de Gemini (GRATIS)

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Clic en **"Create API Key"**
4. Copia la clave generada

### Paso 5: Configurar la API Key

Opción 1 - Variables de entorno (Recomendado):
```powershell
# Copia el archivo de ejemplo
copy .env.example .env

# Edita .env y pega tu API Key
notepad .env
```

Opción 2 - Secrets de Streamlit:
```powershell
# Crear carpeta de configuración
mkdir .streamlit

# Crear archivo secrets.toml
notepad .streamlit\secrets.toml
```

Contenido de `secrets.toml`:
```toml
GEMINI_API_KEY = "tu_api_key_aqui"
```

## ▶️ Ejecutar la Aplicación

```powershell
streamlit run app.py
```

Se abrirá automáticamente en tu navegador en: `http://localhost:8501`

## 💡 Cómo Usar

1. **Escribe tu pregunta** en el cuadro de chat
   - Ejemplo: *"¿Cuál es el estado del cliente Juan Perez?"*
   - Ejemplo: *"Muéstrame los tickets abiertos"*
   - Ejemplo: *"Busca la NAP de la calle Belgrano 123"*

2. **El chatbot hará 3 cosas**:
   - 🤔 Entender qué información necesitas
   - 🔍 Buscar en las Google Sheets
   - ✅ Responderte con datos reales

3. **Ver datos encontrados**: Expande "📊 Ver datos encontrados" para ver la tabla completa

## 📊 Fuentes de Datos

El chatbot consulta estas hojas de Google Sheets:

- **NAPs** (Cajas de distribución)
- **Clientes (NAPs)** (Asignación de clientes a NAPs)
- **Clientes (Cuentas)** (Facturación)
- **Clientes (Datos)** (Información personal)
- **Tickets** (Soporte técnico)
- **Clientes (OLTs)** (Equipos de red)
- **Dashboards** (Métricas generales)

## 🔧 Solución de Problemas

### "No module named 'streamlit'"
```powershell
pip install -r requirements.txt
```

### "API Key no configurada"
Verifica que hayas creado el archivo `.env` o `.streamlit/secrets.toml` con tu clave.

### "Error al cargar Google Sheets"
- Verifica que las hojas estén públicas o compartidas
- Comprueba tu conexión a internet

### Los datos no se actualizan
Usa el botón "🔄 Recargar datos" en el sidebar.

## 🚀 Próximas Mejoras

- [ ] Agregar soporte para PDFs (manuales técnicos)
- [ ] Conectar a base de datos local
- [ ] Exportar conversaciones
- [ ] Agregar autenticación de usuarios
- [ ] Gráficos y visualizaciones

## 📞 Soporte

Si tienes problemas, verifica:
1. Python está instalado correctamente
2. La API Key de Gemini es válida
3. Las dependencias están instaladas
4. Las Google Sheets son accesibles

## 📝 Licencia

Uso interno para USITTEL.

---

**¿Necesitas ayuda?** Revisa la documentación o pregunta en el canal técnico.
