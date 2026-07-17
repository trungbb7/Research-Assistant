import os
import sys
import json
import traceback
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS

# Add parent directory to sys.path if running directly as a script
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
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

    def event_stream():
        # Import run_agent_stream from app
        from .app import run_agent_stream
        
        try:
            for update in run_agent_stream(query):
                event_name = update.get("event", "log")
                yield f"event: {event_name}\ndata: {json.dumps(update, ensure_ascii=False)}\n\n"
        except Exception as e:
            err_msg = {
                "event": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            yield f"event: error\ndata: {json.dumps(err_msg, ensure_ascii=False)}\n\n"
            
    return Response(event_stream(), mimetype="text/event-stream")

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
