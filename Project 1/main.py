from flask import Flask, jsonify, request
import os
import json

app = Flask(__name__)

data_file = "database.json"

if not os.path.exists(data_file):
    with open(data_file,'w') as f:
        json.dump ({}, f)

def read_data():
    with open(data_file, "r") as f:
        return json.load(f)
    
def write_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/items", methods=["GET"])
def get_items():
    """Get all items."""
    data = read_data()
    return jsonify(data)

@app.route("/item/<string:item_id>", methods=["GET"])
def get_item(item_id):
    """Get a specific item by ID."""
    data = read_data()
    if item_id in data:
        return jsonify({item_id: data[item_id]})
    return jsonify({"error": "Item not found"}), 404

@app.route("/item", methods=["POST"])
def create_item():
    """Create a new item."""
    item = request.json
    if not item or "id" not in item or "value" not in item:
        return jsonify({"error": "Invalid input"}), 400

    data = read_data()
    if item["id"] in data:
        return jsonify({"error": "Item ID already exists"}), 400

    data[item["id"]] = item["value"]
    write_data(data)
    return jsonify({"message": "Item created", "item": item}), 201
@app.route("/item/<string:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an existing item by ID."""
    item = request.json
    if not item or "value" not in item:
        return jsonify({"error": "Invalid input"}), 400

    data = read_data()
    if item_id not in data:
        return jsonify({"error": "Item not found"}), 404

    data[item_id] = item["value"]
    write_data(data)
    return jsonify({"message": "Item updated", "item": {item_id: item["value"]}})

@app.route("/item/<string:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item by ID."""
    data = read_data()
    if item_id not in data:
        return jsonify({"error": "Item not found"}), 404

    del data[item_id]
    write_data(data)
    return jsonify({"message": "Item deleted", "item_id": item_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)