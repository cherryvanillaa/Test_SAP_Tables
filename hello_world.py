import dspy
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar el modelo de lenguaje usando Gemini como backend
lm = dspy.LM('gemini/gemini-pro', 
             api_key=os.getenv('GEMINI_API_KEY'),
             cache=True)  # Habilitamos caché para optimizar
dspy.configure(lm=lm)

# Definir una firma simple para nuestro programa
class HelloWorld(dspy.Signature):
    """Un programa simple que genera un saludo personalizado."""
    name = dspy.InputField(desc="Nombre de la persona a saludar", default="World")
    output = dspy.OutputField(desc="Un mensaje de saludo personalizado")

# Crear el predictor usando ChainOfThought para un razonamiento más elaborado
hello = dspy.ChainOfThought(HelloWorld)

def main():
    try:
        # Ejecutar la predicción
        result = hello(name="World")
        
        # Imprimir el resultado
        print(result.output)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()