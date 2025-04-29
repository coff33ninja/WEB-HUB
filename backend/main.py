from fastapi import FastAPI, UploadFile, File, HTTPException, status, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
import json

MODULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules'))
STATUS_FILE = os.path.join(MODULES_DIR, 'module_status.json')

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, 'r') as f:
        return json.load(f)

def save_status(status):
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)

@app.get("/modules")
def list_modules():
    files = [f for f in os.listdir(MODULES_DIR) if os.path.isfile(os.path.join(MODULES_DIR, f)) and not f.endswith('.pyc') and not f.startswith('__')]
    status = load_status()
    modules = []
    for f in files:
        ext = os.path.splitext(f)[1]
        modules.append({
            "name": f,
            "type": "python" if ext == ".py" else ext.lstrip('.'),
            "status": status.get(f, "inactive")
        })
    return modules

@app.post("/modules/upload")
def upload_module(file: UploadFile = File(...)):
    filename = file.filename
    if not (filename.endswith('.py') or filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="Only .py or .json files allowed.")
    dest = os.path.join(MODULES_DIR, filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    status = load_status()
    status[filename] = "inactive"
    save_status(status)
    return {"success": True, "filename": filename}

@app.post("/modules/{module_name}/toggle")
def toggle_module(module_name: str):
    status = load_status()
    if module_name not in status:
        raise HTTPException(status_code=404, detail="Module not found.")
    status[module_name] = "inactive" if status[module_name] == "active" else "active"
    save_status(status)
    return {"success": True, "status": status[module_name]}

@app.delete("/modules/{module_name}")
def delete_module(module_name: str):
    path = os.path.join(MODULES_DIR, module_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Module not found.")
    os.remove(path)
    status = load_status()
    status.pop(module_name, None)
    save_status(status)
    return {"success": True}
