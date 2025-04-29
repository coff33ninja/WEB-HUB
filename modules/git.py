from nicegui import ui
import subprocess
import os
from pathlib import Path
from core.credentials import get_credentials, get_credential_by_id
import requests


def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Git Manager").classes("text-2xl font-semibold text-gray-100 mb-4")

        # --- Credential Selection ---
        credentials = get_credentials()
        cred_options = [(str(c[0]), f"{c[1]} [{c[2]}] {c[3]}") for c in credentials]
        selected_cred_id = {"id": None}
        if cred_options:
            cred_select = ui.select(
                options=cred_options,
                label="Select Server/Credential (optional)",
            ).classes("bg-gray-600 text-white rounded w-full mb-2")
            def on_cred_change():
                selected_cred_id["id"] = cred_select.value
                refresh_server_info()
            cred_select.on("change", on_cred_change)
        else:
            ui.label("No credentials found. Add in Credentials Manager.").classes("text-red-400 mb-2")

        repo_path = (
            ui.input("Repository Path")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        command_output = (
            ui.textarea("Output")
            .props("readonly")
            .classes("w-full h-40 bg-gray-600 text-gray-100 mb-4")
        )

        # --- Server Info & Monitoring ---
        server_info = ui.column().classes("mb-4")
        repo_list = ui.list().classes("w-full mb-4")

        def refresh_server_info():
            server_info.clear()
            repo_list.clear()
            if not selected_cred_id["id"]:
                return
            cred = get_credential_by_id(int(selected_cred_id["id"]))
            if not cred:
                return
            _, name, server_type, url, username, password, token, extra, _ = cred
            with server_info:
                ui.label(f"Server: {name} [{server_type}] {url}").classes("text-gray-100")
                # Monitoring: Ping/API check
                status = "Unknown"
                if server_type == "gitea":
                    try:
                        r = requests.get(f"{url}/api/v1/version", timeout=5, headers={"Authorization": f"token {token}"} if token else {})
                        if r.status_code == 200:
                            status = f"Online (Gitea v{r.json().get('version','?')})"
                        else:
                            status = f"Error: {r.status_code} {r.text}"
                    except Exception as e:
                        status = f"Offline/Error: {e}"
                elif server_type == "github":
                    try:
                        r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"} if token else {}, timeout=5)
                        if r.status_code == 200:
                            status = f"Online (GitHub user: {r.json().get('login','?')})"
                        else:
                            status = f"Error: {r.status_code} {r.text}"
                    except Exception as e:
                        status = f"Offline/Error: {e}"
                else:
                    status = "No monitoring for this server type."
                ui.label(f"Status: {status}").classes("text-gray-300")

                # List repositories (Gitea/GitHub)
                if server_type == "gitea":
                    try:
                        r = requests.get(f"{url}/api/v1/user/repos", headers={"Authorization": f"token {token}"} if token else {}, timeout=5)
                        if r.status_code == 200:
                            repos = r.json()
                            with repo_list:
                                ui.label("Repositories:").classes("text-gray-200")
                                for repo in repos:
                                    ui.label(f"- {repo['name']}").classes("text-gray-100")
                        else:
                            with repo_list:
                                ui.label(f"Error fetching repos: {r.status_code} {r.text}").classes("text-red-400")
                    except Exception as e:
                        with repo_list:
                            ui.label(f"Error: {e}").classes("text-red-400")
                elif server_type == "github":
                    try:
                        r = requests.get("https://api.github.com/user/repos", headers={"Authorization": f"token {token}"} if token else {}, timeout=5)
                        if r.status_code == 200:
                            repos = r.json()
                            with repo_list:
                                ui.label("Repositories:").classes("text-gray-200")
                                for repo in repos:
                                    ui.label(f"- {repo['name']}").classes("text-gray-100")
                        else:
                            with repo_list:
                                ui.label(f"Error fetching repos: {r.status_code} {r.text}").classes("text-red-400")
                    except Exception as e:
                        with repo_list:
                            ui.label(f"Error: {e}").classes("text-red-400")

        # --- Git Command Execution ---
        def run_git_command(args):
            try:
                repo_input = repo_path.value.strip() or "."
                repo_input = os.path.expanduser(repo_input)
                repo = Path(repo_input)
                if not repo.exists() or not repo.is_dir():
                    command_output.value = f"Error: Repository path '{repo_input}' does not exist or is not a directory."
                    return
                # If credential selected and server_type is github/gitea, set env vars for authentication
                env = os.environ.copy()
                if selected_cred_id["id"]:
                    cred = get_credential_by_id(int(selected_cred_id["id"]))
                    if cred:
                        _, name, server_type, url, username, password, token, extra, _ = cred
                        if server_type == "github":
                            # Use token for HTTPS auth
                            env["GIT_ASKPASS"] = "echo"
                            env["GIT_USERNAME"] = username or ""
                            env["GIT_PASSWORD"] = token or password or ""
                        elif server_type == "gitea":
                            env["GIT_ASKPASS"] = "echo"
                            env["GIT_USERNAME"] = username or ""
                            env["GIT_PASSWORD"] = token or password or ""
                result = subprocess.run(
                    ["git", "-C", str(repo)] + args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                )
                command_output.value = result.stdout + result.stderr
            except Exception as e:
                command_output.value = f"Error: {str(e)}"

        repo_url_input = ui.input("Repository URL").classes("bg-gray-600 text-white rounded w-full mb-2")
        branch_input = ui.input("Branch Name").classes("bg-gray-600 text-white rounded w-full mb-2")
        branch_output = ui.textarea("Branch Output").props("readonly").classes("w-full h-20 bg-gray-600 text-gray-100 mb-4")

        def clone_repo():
            url = repo_url_input.value.strip()
            if url:
                run_git_command(["clone", url])
            else:
                command_output.value = "Error: Repository URL is empty."

        def backup_repo():
            from core.gdrive import upload_file_stub
            import shutil
            repo_input = repo_path.value.strip() or "."
            repo = Path(repo_input)
            if not repo.exists() or not repo.is_dir():
                command_output.value = f"Error: Repository path '{repo_input}' does not exist or is not a directory."
                return
            archive_name = "repo_backup"
            shutil.make_archive(archive_name, "zip", repo)
            upload_file_stub(f"{archive_name}.zip")
            command_output.value = f"Backup created and uploaded as {archive_name}.zip"

        def checkout_branch():
            branch = branch_input.value.strip()
            if branch:
                run_git_command(["checkout", branch])
            else:
                branch_output.value = "Error: Branch name is empty."

        def list_branches():
            try:
                repo_input = repo_path.value.strip() or "."
                repo_input = os.path.expanduser(repo_input)
                repo = Path(repo_input)
                if not repo.exists() or not repo.is_dir():
                    branch_output.value = f"Error: Repository path '{repo_input}' does not exist or is not a directory."
                    return
                result = subprocess.run(
                    ["git", "-C", str(repo), "branch"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                branch_output.value = result.stdout + result.stderr
            except Exception as e:
                branch_output.value = f"Error: {str(e)}"

        with ui.row().classes("mb-4"):
            ui.button("Status", on_click=lambda: run_git_command(["status"]))\
                .classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
            ui.button("Pull", on_click=lambda: run_git_command(["pull"]))\
                .classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
            ui.button("Commit", on_click=lambda: commit_dialog()).classes(
                "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2"
            )
            ui.button("Push", on_click=lambda: run_git_command(["push"]))\
                .classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
            ui.button("Clone", on_click=clone_repo).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
            ui.button("Backup to Drive", on_click=backup_repo).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
            ui.button("Checkout Branch", on_click=checkout_branch).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")
            ui.button("List Branches", on_click=list_branches).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")

        def commit_dialog():
            with ui.dialog().props("persistent") as dialog, ui.card().classes(
                "p-4 bg-gray-700"
            ):
                ui.label("Commit Changes").classes("text-gray-100")
                message = (
                    ui.input("Commit Message")
                    .props("clearable")
                    .classes("bg-gray-600 text-white rounded w-full mb-2")
                )
                with ui.row():
                    ui.button(
                        "Commit",
                        on_click=lambda: [
                            run_git_command(["commit", "-m", message.value]),
                            dialog.close(),
                        ],
                    ).classes(
                        "bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2"
                    )
                    ui.button("Cancel", on_click=dialog.close).classes(
                        "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2"
                    )
            dialog.open()

        # Initial server info refresh
        refresh_server_info()
# Marketplace metadata
def marketplace_info():
    return {
        "name": "Git Manager",
        "description": "Manage Git repositories and credentials",
        "icon": "git",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
