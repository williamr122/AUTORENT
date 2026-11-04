import sys
import os

# Asegurar que el directorio raíz esté en sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Export para Vercel WSGI
app = app

