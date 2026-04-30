import os
import sys

# Add the project root (parent of src) to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import uvicorn
from app.main import app

if __name__ == "__main__":
    # Use reload=True and pass app as a string for development auto-reloading
    uvicorn.run("app.main:app", host="0.0.0.0", port=8086, reload=True)
