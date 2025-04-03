import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('chatroom.db')
    conn.row_factory = sqlite3.Row
    return conn

class MyServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.handle_index()
        elif self.path.startswith('/static/'):
            self.handle_static_files()
        elif self.path == "/post":
            self.do_GET_posts()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_index(self):
        with open('index.html', 'r') as file:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(file.read().encode())

    def do_GET_posts(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT message, timestamp FROM messages ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()

        posts_html = "".join(
            f"""
            <div class="post-container">
                <p>{row[0]}</p>
                <sup>sent: {row[1]}</sup>
            </div>
            """ for row in rows
        )

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(posts_html.encode())

    def do_POST(self):
        if self.path == "/post":
            self.handle_post_request()

    def handle_post_request(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        form = parse_qs(post_data.decode())
        message = form.get('data', [''])[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (message, timestamp) VALUES (?, ?)", (message, timestamp))
        conn.commit()
        conn.close()

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
        <div class="post-container">
            <p>{message}</p>
            <sup>sent: {timestamp}</sup>
        </div>
        """.encode())

    def handle_static_files(self):
        static_dir = os.path.join(os.getcwd(), 'static')
        file_path = os.path.join(static_dir, self.path[8:])

        if os.path.exists(file_path):
            content_type = self.guess_type(file_path)
            with open(file_path, 'rb') as file:
                content = file.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, MyServer)
    print("Server gestartet auf http://localhost:8080")
    httpd.serve_forever()