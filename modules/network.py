from nicegui import ui
import psutil
import time
import socket
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("network_stats.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS network_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent REAL,
            recv REAL,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def render():
    init_db()

    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Network Monitor").classes("text-2xl font-semibold text-gray-100 mb-4")

        # Online status section
        ui.label("Online Status").classes("text-xl mb-4")
        status_label = ui.label()

        def check_online():
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                status_label.set_text("Online")
                status_label.classes(remove="text-red-500", add="text-green-500")
            except Exception:
                status_label.set_text("Offline")
                status_label.classes(remove="text-green-500", add="text-red-500")

        ui.timer(5.0, check_online)
        check_online()

        # Network stats section
        stats_label = ui.label().classes("text-gray-100 mb-4")
        connections_table = ui.table(
            columns=[
                {"name": "local", "label": "Local Address", "field": "local"},
                {"name": "remote", "label": "Remote Address", "field": "remote"},
                {"name": "status", "label": "Status", "field": "status"},
            ],
            rows=[],
        ).classes("w-full bg-gray-600 text-gray-100")

        # Chart.js integration via ui.html and ui.add_body_html
        ui.html("""
        <canvas id="networkChart"></canvas>
        """)
        ui.add_body_html("""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        var ctx = document.getElementById('networkChart').getContext('2d');
        var chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Sent MB/s', data: [], borderColor: '#3b82f6', fill: false },
                    { label: 'Received MB/s', data: [], borderColor: '#10b981', fill: false }
                ]
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        function updateChart(times, sent, recv) {
            chart.data.labels = times;
            chart.data.datasets[0].data = sent;
            chart.data.datasets[1].data = recv;
            chart.update();
        }
        </script>
        """)

        last_bytes_sent = psutil.net_io_counters().bytes_sent
        last_bytes_recv = psutil.net_io_counters().bytes_recv
        times = []
        sent_data = []
        recv_data = []

        def update_stats():
            nonlocal last_bytes_sent, last_bytes_recv
            io = psutil.net_io_counters()
            sent_mb = (io.bytes_sent - last_bytes_sent) / 1024 / 1024
            recv_mb = (io.bytes_recv - last_bytes_recv) / 1024 / 1024
            last_bytes_sent = io.bytes_sent
            last_bytes_recv = io.bytes_recv
            stats_label.set_text(
                f"Sent: {sent_mb:.2f} MB/s | Received: {recv_mb:.2f} MB/s"
            )
            times.append(time.strftime("%H:%M:%S"))
            sent_data.append(sent_mb)
            recv_data.append(recv_mb)
            if len(times) > 20:
                times.pop(0)
                sent_data.pop(0)
                recv_data.pop(0)

            # Insert bandwidth usage into SQLite
            conn = sqlite3.connect("network_stats.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO network_stats (sent, recv, timestamp) VALUES (?, ?, ?)",
                (sent_mb, recv_mb, datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()

            rows = []
            for conn_info in psutil.net_connections():
                try:
                    rows.append(
                        {
                            "local": f"{conn_info.laddr.ip}:{conn_info.laddr.port}",
                            "remote": (
                                f"{conn_info.raddr.ip}:{conn_info.raddr.port}"
                                if conn_info.raddr
                                else "-"
                            ),
                            "status": conn_info.status,
                        }
                    )
                except Exception:
                    continue
            connections_table.rows = rows
            connections_table.update()

            # Update Chart.js chart via JS
            ui.run_javascript(f"updateChart({times}, {sent_data}, {recv_data})")

        ui.timer(1.0, update_stats)
        update_stats()

# Marketplace metadata
def marketplace_info():
    return {
        "name": "Network Monitor",
        "description": "Monitor network status and bandwidth usage",
        "icon": "network_check",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
