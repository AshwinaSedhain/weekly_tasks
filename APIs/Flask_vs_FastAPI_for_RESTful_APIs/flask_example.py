from flask import Flask, request, jsonify

app = Flask(__name__)

# Fake database
users = [
    {"id": 1, "name": "Ashwini"},
    {"id": 2, "name": "Sital"}
]

# GET all users
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

# POST a new user
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = {"id": len(users)+1, "name": data["name"]}
    users.append(new_user)
    return jsonify(new_user), 201

# Run the server
if __name__ == '__main__':
    app.run(debug=True)