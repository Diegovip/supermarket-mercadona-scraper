import os
import json
import requests
from supabase import create_client, Client

# Lee variables de entorno (configúralas en GitHub Secrets)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Carga el archivo JSON con los productos
with open("data.json", "r", encoding="utf-8") as f:
    productos = json.load(f)

# Limpia y transforma datos si es necesario
datos_limpios = []
for item in productos:
    datos_limpios.append({
        "nombre": item.get("name"),
        "precio": item.get("price"),
        "unidad": item.get("unit"),
        "categoria": item.get("category"),
        "supermercado": "Mercadona"
    })

# Borra todo antes (opcional, para mantener datos actualizados sin duplicados)
supabase.table("ingredientes").delete().neq("id", 0).execute()

# Inserta los nuevos productos
res = supabase.table("ingredientes").insert(datos_limpios).execute()
print("Datos subidos correctamente:", res)
