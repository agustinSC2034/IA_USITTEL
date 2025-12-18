"""
Script de prueba para verificar la conexión con Gemini
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Obtener API key
api_key = os.getenv("GEMINI_API_KEY")

print("=" * 60)
print("TEST DE CONEXIÓN CON GEMINI")
print("=" * 60)

if not api_key:
    print("❌ ERROR: No se encontró la API Key")
    print("Verifica que el archivo .env tenga la clave")
else:
    print(f"✅ API Key encontrada: {api_key[:20]}...")

print("\nProbando conexión...")

try:
    # Configurar Gemini
    genai.configure(api_key=api_key)
    
    # Listar modelos disponibles
    print("\n📋 MODELOS DISPONIBLES:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    # Probar con el primer modelo disponible
    print("\n🤖 Enviando pregunta a Gemini...")
    model = genai.GenerativeModel('gemini-pro-latest')
    
    # Prueba simple
    response = model.generate_content("Di solo 'Hola, funciono correctamente'")
    
    print("\n✅ RESPUESTA DE GEMINI:")
    print(response.text)
    print("\n🎉 ¡La conexión funciona perfectamente!")
    
except Exception as e:
    print(f"\n❌ ERROR AL CONECTAR CON GEMINI:")
    print(f"Tipo de error: {type(e).__name__}")
    print(f"Mensaje: {str(e)}")
    
print("\n" + "=" * 60)
