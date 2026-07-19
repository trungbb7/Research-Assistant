import os
import sys
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
from agent import event_stream
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to sys.path if running directly as a script
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def research():
    data = request.get_json() or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Vui lòng nhập câu hỏi hoặc chủ đề nghiên cứu."}), 400

    return Response(event_stream(query), mimetype="text/event-stream")


if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

if __name__ == "__main__":
    # Run the web application locally
    print("Starting AI Research Assistant web app at http://localhost:5000...")
    app.run(host="127.0.0.1", port=5000, debug=True)
