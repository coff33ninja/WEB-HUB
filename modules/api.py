from nicegui import ui
import requests
import sqlite3
import json
import datetime

def init_db():
    conn=sqlite3.connect("links.db")
    c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS api_endpoints (id INTEGER PRIMARY KEY, name TEXT, url TEXT, method TEXT, headers TEXT, payload TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS api_history (
                    id INTEGER PRIMARY KEY,
                    endpoint_id INTEGER,
                    status INTEGER,
                    response TEXT,
                    timestamp TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("API Tester").classes("text-2xl font-semibold text-gray-100 mb-4")
        name=ui.input("Endpoint Name").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        url=ui.input("URL").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        method=ui.select(["GET","POST","PUT","DELETE"],value="GET").classes("bg-gray-600 text-white rounded w-full mb-2")
        headers=ui.textarea("Headers (JSON)").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        payload=ui.textarea("Payload (JSON)").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        response=ui.textarea("Response").props("readonly").classes("w-full h-40 bg-gray-600 text-gray-100 mb-4")
        endpoints_list=ui.list().classes("w-full")
        history_list=ui.list().classes("w-full h-40 overflow-auto bg-gray-600 text-gray-100 rounded p-2 mb-4")

        def load_endpoints():
            conn=sqlite3.connect("links.db")
            c=conn.cursor()
            c.execute("SELECT id,name,url,method,headers,payload FROM api_endpoints")
            return c.fetchall()

        def save_endpoint():
            try:
                headers_json=json.loads(headers.value) if headers.value else {}
                payload_json=json.loads(payload.value) if payload.value else {}
                conn=sqlite3.connect("links.db")
                c=conn.cursor()
                c.execute("INSERT INTO api_endpoints (name,url,method,headers,payload) VALUES (?,?,?,?,?)",(name.value or url.value,url.value,method.value,json.dumps(headers_json),json.dumps(payload_json)))
                conn.commit()
                conn.close()
                refresh_endpoints()
            except Exception as e:
                ui.notify(f"Error saving endpoint: {str(e)}",type="negative")

        def delete_endpoint(endpoint_id):
            conn=sqlite3.connect("links.db")
            c=conn.cursor()
            c.execute("DELETE FROM api_endpoints WHERE id=?",(endpoint_id,))
            c.execute("DELETE FROM api_history WHERE endpoint_id=?",(endpoint_id,))
            conn.commit()
            conn.close()
            refresh_endpoints()
            history_list.clear()

        def save_response_history(endpoint_id,status,response_text):
            conn=sqlite3.connect("links.db")
            c=conn.cursor()
            timestamp=datetime.datetime.now().isoformat()
            c.execute("INSERT INTO api_history (endpoint_id,status,response,timestamp) VALUES (?,?,?,?)",(endpoint_id,status,response_text,timestamp))
            conn.commit()
            conn.close()

        def load_history(endpoint_id):
            conn=sqlite3.connect("links.db")
            c=conn.cursor()
            c.execute("SELECT status,response,timestamp FROM api_history WHERE endpoint_id=? ORDER BY timestamp DESC LIMIT 10",(endpoint_id,))
            return c.fetchall()

        uploaded_file={"name":None,"content":None}

        def handle_file_upload(e):
            uploaded_file["name"]=e.name
            uploaded_file["content"]=e.content.read()
            ui.notify(f"File '{e.name}' uploaded",type="positive")

        ui.upload(on_upload=lambda e: handle_file_upload(e)).props("label=Upload File for POST").classes("bg-gray-600 text-white rounded mb-2")

        def test_endpoint():
            try:
                headers_json=json.loads(headers.value) if headers.value else {}
                payload_json=json.loads(payload.value) if payload.value else {}
                files=None
                if method.value=="POST" and uploaded_file["name"] and uploaded_file["content"]:
                    files={"file":(uploaded_file["name"],uploaded_file["content"])}
                response_data=requests.request(method.value,url.value,headers=headers_json,json=payload_json if not files else None,files=files,timeout=5)
                response.value=f"Status: {response_data.status_code}\n\n{response_data.text}"
                conn=sqlite3.connect("links.db")
                c=conn.cursor()
                c.execute("SELECT id FROM api_endpoints WHERE url=? AND method=?",(url.value,method.value))
                row=c.fetchone()
                if row:
                    save_response_history(row[0],response_data.status_code,response_data.text)
                    refresh_history(row[0])
                conn.close()
            except Exception as e:
                response.value=f"Error: {str(e)}"

        def load_endpoint(endpoint):
            endpoint_id,ep_name,ep_url,ep_method,ep_headers,ep_payload=endpoint
            name.value=ep_name
            url.value=ep_url
            method.value=ep_method
            headers.value=json.dumps(json.loads(ep_headers),indent=2) if ep_headers else ""
            payload.value=json.dumps(json.loads(ep_payload),indent=2) if ep_payload else ""
            refresh_history(endpoint_id)

        def refresh_endpoints():
            endpoints_list.clear()
            for endpoint_id,ep_name,ep_url,ep_method,_,_ in load_endpoints():
                with endpoints_list:
                    with ui.row().classes("items-center"):
                        ui.label(ep_name or ep_url).classes("text-gray-100")
                        ui.button("Load",on_click=lambda e=(endpoint_id,ep_name,ep_url,ep_method,_,_): load_endpoint(e)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")
                        ui.button("Delete",on_click=lambda e=endpoint_id: delete_endpoint(e)).classes("bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1")

        def refresh_history(endpoint_id):
            history_list.clear()
            history=load_history(endpoint_id)
            for status,resp,timestamp in history:
                with history_list:
                    ui.label(f"[{timestamp}] Status: {status}").classes("font-bold")
                    ui.label(resp).classes("whitespace-pre-wrap mb-2")

        def export_endpoints():
            from core.gdrive import upload_file_stub
            endpoints=load_endpoints()
            with open("endpoints.json","w") as f:
                json.dump([{"id":e[0],"name":e[1],"url":e[2],"method":e[3],"headers":e[4],"payload":e[5]} for e in endpoints],f)
            upload_file_stub("endpoints.json")
            ui.notify("Endpoints exported to Google Drive",type="positive")

        ui.button("Test",on_click=test_endpoint).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-2")
        ui.button("Save Endpoint",on_click=save_endpoint).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2 mb-2")
        ui.button("Export to Drive",on_click=export_endpoints).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        refresh_endpoints()

# Marketplace metadata
def marketplace_info():
    return {
        "name": "API Tester",
        "description": "Test and manage API endpoints",
        "icon": "api",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
