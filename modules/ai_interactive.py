from nicegui import ui
import ollama
import subprocess
import sqlite3
import re
import os
import importlib.util
import datetime

DB_FILE = "links.db"
RESTRICTED_MODULES = ["os", "sys", "subprocess", "shutil", "socket"]
ALLOWED_EXTENSIONS = [".py"]
CORE_MODULES_PATH = "core"  # Path to the core modules folder


def init_db():
    """Initialize the database for storing prompt history and settings."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT,
                response TEXT,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )
        conn.commit()


def save_prompt_history(prompt, response, model):
    """Save a prompt and response to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ai_prompts (prompt, response, model) VALUES (?, ?, ?)",
            (prompt, response, model),
        )
        conn.commit()


def load_prompt_history(limit=5):
    """Load recent prompts from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT prompt, response, model, timestamp FROM ai_prompts ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return c.fetchall()


def save_setting(key, value):
    """Save a setting to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO ai_settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        conn.commit()


def load_setting(key, default):
    """Load a setting from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM ai_settings WHERE key = ?", (key,))
        result = c.fetchone()
        if result:
            try:
                return eval(
                    result[0], {}, {}
                )  # Safely evaluate string to Python object
            except Exception:
                return default
        return default


def validate_filename(filename):
    """Validate file name to prevent directory traversal and ensure correct extension."""
    if not filename.endswith(tuple(ALLOWED_EXTENSIONS)):
        return False, "Only .py files are allowed."
    if re.search(r"[\/\\:*\?\"<>|]", filename):
        return False, "Invalid characters in file name."
    return True, ""


def get_available_models():
    """Fetch available Ollama models."""
    try:
        models = ollama.list()
        if isinstance(models, dict) and "models" in models:
            return [model.get("name", str(model)) for model in models["models"]]
        elif isinstance(models, list):
            return [str(model) for model in models]
        else:
            return [str(models)]
    except Exception as e:
        ui.notify(f"Error fetching models: {str(e)}", type="negative")
        return []


def send_prompt(
    prompt,
    output_area,
    save_button,
    run_button,
    copy_button,
    preview_button,
    model,
    loading_dialog,
    auto_execute,
    auto_preview,
    preview_area,
):
    """Send a prompt to the Ollama model and process the response."""
    if not prompt.strip():
        ui.notify("Please enter a task or question.", type="warning")
        loading_dialog.close()
        return None

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert coder building modules for a NiceGUI-based Homepage Dashboard. "
                "Generate Python scripts that are compatible with the dashboard’s architecture. Each script must include:\n"
                "- A `render()` function using NiceGUI with Tailwind CSS classes (e.g., 'p-6 bg-gray-700 text-gray-100').\n"
                "- An `init_db()` function to create tables in 'links.db' using sqlite3.\n"
                "- A `marketplace_info` dictionary with metadata (name, description, icon, etc.).\n"
                "- Integration with core modules like 'settings.py' and 'gdrive.py' (e.g., Google Drive sync via 'upload_file_stub').\n"
                "Use safe code, avoiding restricted modules: {', '.join(RESTRICTED_MODULES)}. "
                "Provide code in ```python\n...\n``` blocks. If the prompt is not for code generation, explain clearly."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"max_tokens": 3000, "temperature": 0.7},
        )
        content = response["message"]["content"]
        save_prompt_history(prompt, content, model)

        start = content.find("```python\n") + 10
        end = content.rfind("```")
        if start > 9 and end > start:
            last_code = content[start:end].strip()
            output_area.set_text(f"Generated Code:\n{last_code}")
            save_button.props("disabled=false")
            run_button.props("disabled=false")
            copy_button.props("disabled=false")
            preview_button.props("disabled=false")
            ui.run_javascript("Prism.highlightAll();")  # Apply syntax highlighting

            # Auto-execute or auto-preview if enabled
            if auto_execute:
                run_code(last_code, output_area, True, loading_dialog)
            elif auto_preview:
                preview_code(last_code, preview_area)
            return last_code
        else:
            output_area.set_text(f"Response:\n{content}")
            save_button.props("disabled=true")
            run_button.props("disabled=true")
            copy_button.props("disabled=true")
            preview_button.props("disabled=true")
            return None
    except Exception as e:
        output_area.set_text(f"Error: {str(e)}")
        save_button.props("disabled=true")
        run_button.props("disabled=true")
        copy_button.props("disabled=true")
        preview_button.props("disabled=true")
        return None
    finally:
        loading_dialog.close()


def save_code(last_code):
    """Save the generated code to a file, optionally to the core modules folder."""
    if not last_code:
        ui.notify("No code to save.", type="warning")
        return

    with ui.dialog() as dialog, ui.card().classes("p-4"):
        ui.label("Save Code").classes("text-lg font-semibold")
        file_name_input = ui.input(
            "File name (e.g., module.py)", value="module.py"
        ).classes("w-full mb-2")
        save_to_core = ui.checkbox("Save to core modules folder", value=False).classes(
            "text-gray-100 mb-2"
        )

        def save():
            file_name = file_name_input.value.strip()
            valid, error = validate_filename(file_name)
            if not valid:
                ui.notify(error, type="negative")
                return
            try:
                save_path = (
                    os.path.join(CORE_MODULES_PATH, file_name)
                    if save_to_core.value
                    else file_name
                )
                os.makedirs(CORE_MODULES_PATH, exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(last_code)
                ui.notify(f"Code saved to {save_path}", type="positive")
                dialog.close()
            except Exception as e:
                ui.notify(f"Failed to save code: {str(e)}", type="negative")

        ui.button("Save", on_click=save).classes(
            "bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2"
        )
        ui.button("Cancel", on_click=dialog.close).classes(
            "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2"
        )


def run_code(last_code, output_area, restrict_execution, loading_dialog):
    """Run the generated code in a safe environment."""
    if not last_code:
        ui.notify("No code to run.", type="warning")
        loading_dialog.close()
        return

    temp_file = "temp_script.py"
    try:
        if restrict_execution and any(
            module in last_code for module in RESTRICTED_MODULES
        ):
            output_area.set_text(
                f"Error: Code contains restricted modules: {', '.join(RESTRICTED_MODULES)}"
            )
            loading_dialog.close()
            return

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(last_code)

        result = subprocess.run(
            ["python", temp_file], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            output_area.set_text(f"Output:\n{result.stdout}")
        else:
            output_area.set_text(f"Error:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        output_area.set_text("Error: Code execution timed out after 10 seconds.")
    except Exception as e:
        output_area.set_text(f"Error running code: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        loading_dialog.close()


def copy_code(last_code):
    """Copy the generated code to the clipboard."""
    if last_code:
        escaped_code = last_code.replace("`", "\\`")
        ui.run_javascript(f"navigator.clipboard.writeText(`{escaped_code}`)")
        ui.notify("Code copied to clipboard!", type="positive")
    else:
        ui.notify("No code to copy.", type="warning")


def preview_code(last_code, preview_area):
    """Preview the generated module’s UI in a dialog."""
    if not last_code:
        ui.notify("No code to preview.", type="warning")
        return

    with ui.dialog() as dialog, ui.card().classes("p-4 max-w-4xl"):
        ui.label("Module Preview").classes("text-lg font-semibold mb-4")
        preview_area.clear()
        try:
            temp_file = "temp_preview.py"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(last_code)
            spec = importlib.util.spec_from_file_location("temp_preview", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "render"):
                with preview_area:
                    module.render()
            else:
                ui.label("Error: Module lacks a render() function.").classes(
                    "text-red-400"
                )
            os.remove(temp_file)
        except Exception as e:
            ui.label(f"Error previewing module: {str(e)}").classes("text-red-400")
        ui.button("Close", on_click=dialog.close).classes(
            "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2 mt-4"
        )
    dialog.open()


def upload_file(prompt_input):
    """Upload a Python file to populate the prompt with its contents."""

    def handle_upload(e):
        try:
            content = e.content.read().decode("utf-8")
            prompt_input.set_value(
                f"Edit the following code:\n```python\n{content}\n```"
            )
            ui.notify("File uploaded and added to prompt.", type="positive")
        except Exception as e:
            ui.notify(f"Error reading file: {str(e)}", type="negative")

    ui.upload(on_upload=handle_upload, auto_upload=True).props(
        "accept=.py label=Upload Python File"
    ).classes("bg-gray-600 text-white rounded mb-2")


def show_history(prompt_input):
    """Show recent prompt history in a dialog with copy-to-prompt option."""
    with ui.dialog() as dialog, ui.card().classes("p-4 max-w-3xl"):
        ui.label("Prompt History").classes("text-lg font-semibold mb-4")
        history = load_prompt_history()
        if not history:
            ui.label("No history available.").classes("text-gray-400")
        else:
            for prompt, response, model, timestamp in history:
                with ui.expansion(f"{timestamp} - {prompt[:50]}...").classes("mb-2"):
                    ui.label("Prompt:").classes("font-semibold")
                    ui.label(prompt).classes("text-gray-300 mb-2")
                    ui.label("Response:").classes("font-semibold")
                    ui.label(response).classes("text-gray-300")
                    ui.label(f"Model: {model}").classes("text-gray-400 text-sm")
                    ui.button(
                        "Copy to Prompt",
                        on_click=lambda p=prompt: [
                            prompt_input.set_value(p),
                            dialog.close(),
                        ],
                    ).classes(
                        "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mt-2"
                    )
        ui.button("Close", on_click=dialog.close).classes(
            "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2 mt-4"
        )
    dialog.open()


def render():
    """Render the AI Interactive module UI."""
    init_db()
    last_code = [None]  # Use list to allow modification in nested functions
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("AI Code Assistant").classes(
            "text-2xl font-semibold text-gray-100 mb-4"
        )

        # Load Prism.js for syntax highlighting
        ui.add_head_html(
            """
            <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
        """
        )

        # Model selection
        available_models = get_available_models()
        default_model = load_setting(
            "selected_model", available_models[0] if available_models else ""
        )
        model_select = ui.select(
            available_models, value=default_model, label="Ollama Model"
        ).classes("w-full mb-2 bg-gray-600 text-white rounded")
        model_select.on("change", lambda e: save_setting("selected_model", e.value))

        # Prompt templates
        templates = {
            "Task Tracker": "Create a NiceGUI module for a task tracker with a SQLite database, Google Drive sync, and Tailwind CSS styling.",
            "Calendar": "Create a NiceGUI module for a calendar with event management, SQLite storage, and Google Calendar integration.",
            "Weather Widget": "Create a NiceGUI module for a weather widget using OpenWeatherMap API and Tailwind CSS.",
        }
        with ui.row().classes("w-full mb-2"):
            template_select = ui.select(
                ["Custom"] + list(templates.keys()),
                value="Custom",
                label="Prompt Template",
            ).classes("w-1/4 bg-gray-600 text-white rounded")
            prompt_input = (
                ui.textarea(
                    placeholder="Enter your coding task or select a template..."
                )
                .props("autofocus")
                .classes("w-3/4 bg-gray-600 text-white rounded")
            )

            def update_prompt():
                if template_select.value != "Custom":
                    prompt_input.set_value(templates[template_select.value])

            template_select.on("change", update_prompt)

        # Input and options
        with ui.row().classes("w-full mb-4"):
            char_count = ui.label("0/2000").classes("text-gray-400 text-sm mt-1")
            prompt_input.on(
                "input", lambda e: char_count.set_text(f"{len(e.value)}/2000")
            )
            with ui.column():
                restrict_execution = ui.checkbox(
                    "Restrict Execution", value=True
                ).classes("text-gray-100")
                auto_execute = ui.checkbox("Auto-Execute Code", value=False).classes(
                    "text-gray-100"
                )
                auto_preview = ui.checkbox("Auto-Preview Module", value=False).classes(
                    "text-gray-100"
                )
                ui.button(
                    "Upload File", on_click=lambda: upload_file(prompt_input)
                ).classes("bg-gray-600 text-white rounded px-4 py-2")
                ui.button(
                    "View History", on_click=lambda: show_history(prompt_input)
                ).classes("bg-gray-600 text-white rounded px-4 py-2")

        # Output and preview split layout
        with ui.splitter().classes("w-full h-96 mb-4") as splitter:
            with splitter.first:
                output_area = (
                    ui.textarea(value="")
                    .props("readonly")
                    .classes("w-full h-full bg-gray-800 text-white rounded")
                )
            with splitter.second:
                preview_area = ui.element("div").classes(
                    "w-full h-full bg-gray-800 rounded p-4 overflow-auto"
                )

        # Buttons
        with ui.row():

            def handle_send():
                with ui.dialog() as loading_dialog, ui.card().classes("p-4"):
                    ui.label("Processing...").classes("text-gray-100")
                    ui.spinner(size="lg")
                loading_dialog.open()
                last_code[0] = send_prompt(
                    prompt_input.value,
                    output_area,
                    save_button,
                    run_button,
                    copy_button,
                    preview_button,
                    model_select.value,
                    loading_dialog,
                    auto_execute.value,
                    auto_preview.value,
                    preview_area,
                )

            def handle_run():
                with ui.dialog() as loading_dialog, ui.card().classes("p-4"):
                    ui.label("Running Code...").classes("text-gray-100")
                    ui.spinner(size="lg")
                loading_dialog.open()
                run_code(
                    last_code[0], output_area, restrict_execution.value, loading_dialog
                )

            ui.button("Generate", on_click=handle_send).classes(
                "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2"
            )
            save_button = (
                ui.button("Save Code", on_click=lambda: save_code(last_code[0]))
                .props("disabled")
                .classes(
                    "bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2 ml-2"
                )
            )
            run_button = (
                ui.button("Run Code", on_click=handle_run)
                .props("disabled")
                .classes(
                    "bg-purple-600 hover:bg-purple-500 text-white rounded px-4 py-2 ml-2"
                )
            )
            copy_button = (
                ui.button("Copy Code", on_click=lambda: copy_code(last_code[0]))
                .props("disabled")
                .classes(
                    "bg-indigo-600 hover:bg-indigo-500 text-white rounded px-4 py-2 ml-2"
                )
            )
            preview_button = (
                ui.button(
                    "Preview Module",
                    on_click=lambda: preview_code(last_code[0], preview_area),
                )
                .props("disabled")
                .classes(
                    "bg-teal-600 hover:bg-teal-500 text-white rounded px-4 py-2 ml-2"
                )
            )
            ui.button(
                "Clear",
                on_click=lambda: [
                    prompt_input.set_value(""),
                    output_area.set_text(""),
                    preview_area.clear(),
                    save_button.props("disabled=true"),
                    run_button.props("disabled=true"),
                    copy_button.props("disabled=true"),
                    preview_button.props("disabled=true"),
                    char_count.set_text("0/2000"),
                ],
            ).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2 ml-2")


def marketplace_info():
    """Return metadata for the Marketplace."""
    return {
        "name": "AI Code Assistant",
        "description": "Generate, preview, and execute NiceGUI modules on the fly using Ollama models, with prompt templates and dynamic integration",
        "icon": "smart_toy",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com",
    }
