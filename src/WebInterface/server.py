from flask import Flask, request, render_template
from waitress import serve

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return "Hello, World!"


if __name__ == "__main__":
    serve(app, debug=True)