# 📝 Anotaciones del Proyecto - Chatbot USITTEL

## 📌 Información General

**Proyecto**: Chatbot interno para consultas de clientes, NAPs, tickets, facturación  
**Tecnología**: Python + Streamlit + Google Gemini AI  
**Costo**: GRATIS (cuota gratuita de Gemini)  
**Fecha de inicio**: 17 de diciembre de 2025

---

## 🔑 Credenciales

### Google Gemini API
- **API Key**: `AIzaSyDSY7VaSqDoKIWId_mhvN5D9X3iqC1ELEc`
- **Nombre**: USITTEL_IA_INTERNA
- **Proyecto**: USITTEL-IA
- **ID Proyecto**: 354729170096
- **Límite gratis**: 60 consultas por minuto
- **Documentación**: https://ai.google.dev/

⚠️ **IMPORTANTE**: La API Key está en el archivo `.env` - NUNCA subir este archivo a GitHub

---

## 🏗️ Arquitectura del Sistema (RAG)

El chatbot funciona en 3 pasos:

### 1️⃣ ROUTER (IA)
- Recibe la pregunta del usuario
- Analiza dónde buscar (qué hoja de Google Sheets)
- Identifica qué columna y qué valor buscar
- Retorna un JSON con los parámetros

**Ejemplo**:
```
Usuario: "¿Cuál es el estado de Juan Perez?"
Router: {
  "dataframe": "clientes_datos",
  "columna": "Nombre",
  "valor": "Juan Perez"
}
```

### 2️⃣ MOTOR DE BÚSQUEDA (Python/Pandas)
- Ejecuta búsqueda exacta en el DataFrame
- NO inventa datos, solo busca
- Si no encuentra, retorna vacío

**Código**:
```python
df[df['Nombre'].str.contains('Juan Perez', case=False)]
```

### 3️⃣ SINTETIZADOR (IA)
- Recibe SOLO los datos encontrados
- Genera respuesta amable y profesional
- Si no hay datos, informa que no se encontró nada

---

## 📊 Fuentes de Datos

### Google Sheets conectadas:

1. **NAPs (Cajas)** - gid: 443573341
2. **Clientes_naps** - gid: 443573341
3. **Clientes_cuentas (Facturación)** - gid: 101720087
4. **Clientes_datos (Personales)** - gid: 1694258191
5. **Tickets (Soporte)** - gid: 0
6. **Clientes_OLTs** - gid: 819538991
7. **Dashboards** - gid: 44575307

**URL base**: `https://docs.google.com/spreadsheets/d/1OjVaDvgzWyxDEY4u-3OJrQ8KIFUSpvMOvNT73VZb-FE/`

**Actualización**: Cada 60 segundos (cache TTL configurado)

---

## 🛠️ Dependencias Instaladas

```
streamlit==1.29.0          # Framework web
pandas==2.1.4              # Análisis de datos
google-generativeai==0.3.2 # API Gemini
python-dotenv==1.0.0       # Variables de entorno
```

---

## 📁 Estructura del Proyecto

```
IA_USITTEL/
│
├── app.py                 # Aplicación principal
├── requirements.txt       # Dependencias
├── .env                   # API Keys (NO SUBIR A GIT)
├── .env.example          # Ejemplo de configuración
├── .gitignore            # Archivos a ignorar en Git
├── README.md             # Documentación
├── contexto.md           # Contexto original
└── anotaciones_sobre_el_proyecto.md  # Este archivo
```

---

## 🚀 Cómo Ejecutar Localmente

### Primera vez:
```powershell
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

### Próximas veces:
```powershell
streamlit run app.py
```

La app abrirá en: `http://localhost:8501`

---

## 🌐 Deployment (Compartir con el Equipo)

### Opción Recomendada: Streamlit Cloud (GRATIS) ⭐

#### Paso 1: Crear repositorio en GitHub
1. Ir a https://github.com/new
2. Crear repositorio llamado `chatbot-usittel`
3. Marcar como **Privado** (para proteger datos)

#### Paso 2: Subir el código
```powershell
git init
git add .
git commit -m "Initial commit - Chatbot USITTEL"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/chatbot-usittel.git
git push -u origin main
```

⚠️ **IMPORTANTE**: NO subir el archivo `.env` (ya está en .gitignore)

#### Paso 3: Desplegar en Streamlit Cloud
1. Ir a https://share.streamlit.io/
2. Conectar tu cuenta de GitHub
3. Seleccionar el repositorio `chatbot-usittel`
4. En **Advanced settings**, agregar:
   ```
   GEMINI_API_KEY = AIzaSyDSY7VaSqDoKIWId_mhvN5D9X3iqC1ELEc
   ```
5. Clic en **Deploy**

#### Resultado:
- URL pública: `https://chatbot-usittel.streamlit.app`
- Cada persona puede abrir esa URL
- Cada uno tiene su propia conversación (no se comparten mensajes)

### Agregar Autenticación (Opcional)
Si quieres que solo tu equipo acceda, puedes agregar contraseña:

```python
# En app.py, agregar al inicio:
import streamlit_authenticator as stauth

# Configurar usuarios permitidos
names = ['Usuario1', 'Usuario2']
usernames = ['user1', 'user2']
passwords = ['pass1', 'pass2']
```

---

## 🔮 Mejoras Futuras

### Corto plazo:
- [ ] Agregar autenticación de usuarios
- [ ] Exportar conversaciones a PDF
- [ ] Gráficos y visualizaciones
- [ ] Historial persistente (guardar conversaciones)

### Mediano plazo:
- [ ] Agregar PDFs (manuales técnicos)
- [ ] Conectar a base de datos local (MySQL/PostgreSQL)
- [ ] Búsqueda semántica (embeddings)
- [ ] Notificaciones automáticas

### Largo plazo:
- [ ] Integración con WhatsApp Business
- [ ] Dashboard de métricas de uso
- [ ] Modelo fine-tuned específico para USITTEL

---

## 🔧 Solución de Problemas

### Error: "No module named 'streamlit'"
**Solución**: `pip install -r requirements.txt`

### Error: "API Key no configurada"
**Solución**: Verificar que existe el archivo `.env` con la API Key

### Error al cargar Google Sheets
**Solución**: 
1. Verificar que las hojas estén públicas
2. Comprobar conexión a internet
3. Revisar los GIDs de las hojas

### Los datos no se actualizan
**Solución**: Usar el botón "🔄 Recargar datos" en el sidebar

---

## 💡 Preguntas Frecuentes

### ¿Cada usuario tiene su propia conversación?
**SÍ**. Streamlit crea una sesión independiente para cada navegador.

### ¿Cuánto cuesta mantener esto?
**GRATIS**. Gemini tiene 60 llamadas/minuto gratis. Si se supera, puedes usar gpt-4o-mini (~$0.15 por millón de tokens).

### ¿Se pueden agregar más fuentes de datos?
**SÍ**. Solo agregar nuevas funciones de carga:
- PDFs → `PyPDF2` o `pdfplumber`
- Excel locales → `pandas.read_excel()`
- Bases de datos → `sqlalchemy`

### ¿Es seguro?
**SÍ**, siempre que:
- No subas `.env` a GitHub
- Mantengas el repositorio privado
- Uses Streamlit Cloud con secretos configurados

---

## 📞 Contacto y Soporte

**Desarrollador**: [Tu nombre]  
**Fecha última actualización**: 17 de diciembre de 2025  
**Versión**: 1.0.0

---

## 📚 Recursos Útiles

- [Documentación Streamlit](https://docs.streamlit.io/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Pandas Docs](https://pandas.pydata.org/docs/)
- [Deploy en Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud/get-started)

---

**🎉 ¡Proyecto listo para usar!**
