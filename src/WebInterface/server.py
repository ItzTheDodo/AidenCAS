from typing import Any

from flask import Flask, request, render_template, jsonify
from waitress import serve

from Core.Function.FunctionInterpreter.Function import Function
from Core.Namespace.Namespace import Namespace

namespace = Namespace("main")

app = Flask(__name__, static_url_path='/static')

def define_function(definition: str) -> tuple[bool, str]:
    try:
        f = Function(definition, namespace)
        return True, f.name
    except Exception as e:
        return False, str(e)

def evaluate_function(name: str, point: float) -> tuple[bool, Any]:
    try:
        func = namespace.functions[name]
        return True, func.evaluate(point)
    except Exception as e:
        return False, str(e)

def batch_evaluate_points(name: str, points: list[float]) -> list[Any]:
    return list(
        evaluate_function(name, point)[1]
        for point in points
    )

@app.route("/batch_evaluate")
def batch_evaluate():
    name = request.args.get("name")
    points_str = request.args.get("points")

    if not name:
        return jsonify({"ok": False, "error": "Missing required query parameter: name"}), 400

    if not points_str:
        return jsonify({"ok": False, "error": "Missing required query parameter: points"}), 400

    try:
        points = list(map(float, points_str[1:-1].split(",")))
        results = batch_evaluate_points(name, points)
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/evaluate")
def evaluate():
    name = request.args.get("name")
    point = request.args.get("point")

    if not name:
        return jsonify({"ok": False, "error": "Missing required query parameter: name"}), 400

    if point is None:
        return jsonify({"ok": False, "error": "Missing required query parameter: point"}), 400

    try:
        numeric_point = float(point)
        ok, result = evaluate_function(name, numeric_point)
        return jsonify({"ok": ok, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/define_function")
def define():
    definition = request.args.get("definition")

    if not definition:
        return jsonify({"ok": False, "name": "Missing definition"})

    try:
        ok, function_name = define_function(definition)
        return jsonify({"ok": ok, "name": function_name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


if __name__ == "__main__":

    PORT = 8080
    HOST = "0.0.0.0"
    print(f"Started server on {HOST}:{PORT}")

    serve(app, host=HOST, port=PORT)