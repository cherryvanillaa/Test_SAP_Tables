import dspy
import os
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict
from urllib.parse import urljoin
import google.generativeai as genai
from google.api_core import retry

# Cargar variables de entorno
load_dotenv()

# Configurar el modelo de lenguaje usando Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("No se encontró GOOGLE_API_KEY en las variables de ambiente")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# URLs para SAP Datasheet
BASE_URL = "https://www.sapdatasheet.org"
TABLES_URL = urljoin(BASE_URL, "abap/tabl/index-a.html")

class SAPTableAnalyzer(dspy.Signature):
    """Signature para analizar y estructurar información de tablas SAP"""
    table_name = dspy.InputField(desc="Nombre de la tabla SAP")
    table_desc = dspy.InputField(desc="Descripción de la tabla")
    table_fields = dspy.InputField(desc="Lista de campos de la tabla")
    table_info = dspy.OutputField(desc="Información estructurada de la tabla y sus campos")

class SAPIndexAgent:
    def __init__(self):
        self.analyzer = dspy.ChainOfThought(SAPTableAnalyzer)
        self.session = aiohttp.ClientSession()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
    
    async def get_table_list(self, limit: int = 10) -> List[Dict]:
        """Obtiene la lista de tablas SAP desde el índice"""
        try:
            async with self.session.get(TABLES_URL, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    tables = []
                    # Buscar filas con clase sapds-alv que contienen las tablas
                    rows = soup.find_all('tr')
                    
                    for row in rows:
                        if len(tables) >= limit:
                            break
                            
                        cols = row.find_all('td', class_='sapds-alv')
                        if len(cols) >= 5:  # Número, Nombre, Descripción, Categoría, Clase
                            number = cols[0].text.strip()
                            table_link = cols[1].find('a')
                            if table_link:
                                table_info = {
                                    'number': number,
                                    'name': table_link.text.strip(),
                                    'description': cols[2].text.strip(),
                                    'category': cols[3].text.strip(),
                                    'delivery_class': cols[4].text.strip(),
                                    'url': urljoin(BASE_URL, table_link['href'])
                                }
                                tables.append(table_info)
                                print(f"📊 Tabla #{number}: {table_info['name']}")
                                print(f"   📝 {table_info['description']}")
                                print(f"   🏷️  Categoría: {table_info['category']}")
                    
                    if not tables:
                        print("⚠️ No se encontraron tablas en la página")
                    
                    return tables
                return []
        except Exception as e:
            print(f"Error obteniendo lista de tablas: {str(e)}")
            return []

    async def get_table_fields(self, table_url: str) -> List[Dict]:
        """Obtiene los campos de una tabla específica"""
        try:
            async with self.session.get(table_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    fields = []
                    
                    # Buscar todas las tablas que tengan la clase table
                    tables = soup.find_all('table', {'class': 'table'})
                    
                    for table in tables:
                        # Verificar si es la tabla de campos buscando los encabezados característicos
                        headers = table.find_all('th', class_='sapds-alv')
                        header_texts = [h.text.strip() for h in headers]
                        
                        if 'Field' in header_texts and 'DataType' in header_texts:
                            # Obtener los índices de las columnas
                            field_idx = header_texts.index('Field')
                            data_element_idx = header_texts.index('Data Element')
                            domain_idx = header_texts.index('Domain')
                            type_idx = header_texts.index('DataType')
                            length_idx = header_texts.index('Length')
                            decimals_idx = header_texts.index('DecimalPlaces')
                            desc_idx = header_texts.index('Short Description')
                            
                            # Procesar todas las filas después del header
                            rows = table.find_all('tr')
                            header_row = None
                            
                            # Encontrar la fila de header real
                            for i, row in enumerate(rows):
                                if 'Field' in [th.text.strip() for th in row.find_all('th', class_='sapds-alv')]:
                                    header_row = i
                                    break
                            
                            if header_row is not None:
                                # Procesar todas las filas después del header
                                for row in rows[header_row + 1:]:
                                    cols = row.find_all('td', class_='sapds-alv')
                                    if len(cols) >= len(headers):  # Asegurarse que tiene todas las columnas
                                        # Extraer enlaces
                                        field_link = cols[field_idx].find('a')
                                        data_element_link = cols[data_element_idx].find('a')
                                        domain_link = cols[domain_idx].find('a')
                                        
                                        field = {
                                            'field': field_link.text.strip() if field_link else cols[field_idx].text.strip(),
                                            'key': 'X' if row.find('input', {'checked': 'checked'}) else '',
                                            'data_element': {
                                                'name': data_element_link.text.strip() if data_element_link else cols[data_element_idx].text.strip(),
                                                'url': urljoin(BASE_URL, data_element_link['href']) if data_element_link else ''
                                            },
                                            'domain': {
                                                'name': domain_link.text.strip() if domain_link else cols[domain_idx].text.strip(),
                                                'url': urljoin(BASE_URL, domain_link['href']) if domain_link else ''
                                            },
                                            'data_type': cols[type_idx].text.strip(),
                                            'length': cols[length_idx].text.strip(),
                                            'decimals': cols[decimals_idx].text.strip(),
                                            'short_description': cols[desc_idx].text.strip()
                                        }
                                        
                                        # Solo agregar si tiene un nombre de campo válido
                                        if field['field'] and not field['field'].isspace():
                                            fields.append(field)
                                            print(f"🔹 Campo: {field['field']} ({field['data_type']})")
                            
                            # Si encontramos y procesamos la tabla de campos, salimos del loop
                            break
                    
                    if not fields:
                        print("⚠️ No se encontraron campos en la tabla")
                        print("URL:", table_url)
                        print(f"Tablas encontradas: {len(tables)}")
                        if tables:
                            for i, table in enumerate(tables):
                                headers = table.find_all('th', class_='sapds-alv')
                                print(f"Tabla {i+1} - Headers encontrados: {len(headers)}")
                                print(f"Headers: {[h.text.strip() for h in headers]}")
                                rows = table.find_all('tr')
                                print(f"Filas encontradas: {len(rows)}")
                    
                    return fields
                else:
                    print(f"❌ Error en la respuesta HTTP: {response.status}")
                    print("URL:", table_url)
                return []
        except Exception as e:
            print(f"Error obteniendo campos de la tabla: {str(e)}")
            print("URL:", table_url)
            return []

    async def process_tables(self):
        """Procesa las tablas y genera archivos JSON individuales"""
        print("\n🔍 Iniciando búsqueda de tablas SAP...")
        tables = await self.get_table_list()
        
        if not tables:
            print("❌ No se encontraron tablas para procesar")
            return
        
        print(f"\n✅ Se encontraron {len(tables)} tablas")
        
        # Crear directorio para los archivos JSON si no existe
        os.makedirs('sap_tables', exist_ok=True)
        
        for table in tables:
            try:
                print(f"\n📋 Procesando tabla: {table['name']}")
                print(f"   Descripción: {table['description']}")
                print(f"   Categoría: {table['category']}")
                
                # Obtener campos de la tabla
                fields = await self.get_table_fields(table['url'])
                
                if fields:
                    # Crear estructura del JSON
                    table_data = {
                        'number': table['number'],
                        'name': table['name'],
                        'description': table['description'],
                        'category': table['category'],
                        'delivery_class': table['delivery_class'],
                        'fields': fields
                    }
                    
                    # Sanitizar el nombre de la tabla para el archivo
                    safe_name = sanitize_path(table['name'])
                    filename = os.path.join('sap_tables', f"{safe_name}.json")
                    
                    # Guardar en archivo JSON individual
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(table_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Tabla {table['name']} guardada con {len(fields)} campos")
                else:
                    print(f"⚠️  No se encontraron campos para la tabla {table['name']}")
                
            except Exception as e:
                print(f"❌ Error procesando tabla {table['name']}: {str(e)}")

    async def close(self):
        await self.session.close()

def format_handler(value):
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    elif isinstance(value, dict):
        return ', '.join(f"{k}: {v}" for k, v in value.items())
    elif value is None:
        return ''
    return str(value)

class TableProcessor:
    def __init__(self):
        self.format_handler = format_handler
    
    def process_table_fields(self, fields):
        if isinstance(fields, list):
            return [self.format_handler(field) for field in fields]
        return self.format_handler(fields)

def sanitize_path(filename: str) -> str:
    """Sanitiza el nombre del archivo reemplazando caracteres no válidos"""
    # Caracteres no permitidos en nombres de archivo
    invalid_chars = '<>:"/\\|?*'
    
    # Reemplazar caracteres no válidos por guion bajo
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Asegurarse de que el nombre es válido para el sistema de archivos
    return filename.strip('.')

async def main():
    try:
        agent = SAPIndexAgent()
        await agent.process_tables()
        await agent.close()
        print("\n✨ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error en la ejecución: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 