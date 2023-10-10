from consts import HTTP
from database import UserAuth, db, User, UserAuth
from flask import Flask, jsonify, request, session
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from schemas import UserAuthSchema, UserSchema

app_version = "0.1.0"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "The requested URL was not found on the server."}), HTTP.not_found

@app.errorhandler(405)
def page_not_found(error):
    return jsonify({"error": "The method is not allowed for the requested URL."}), HTTP.method_not_allowed

@app.route("/", methods=['GET'])
def index():
    """
    Index request. If logged in, it will return a welcome message with the username,
    and, if not it returns `Hello server`
    """
    # No problem if this fails, so won't enclose it in a try/except
    user_auth_schema = UserAuthSchema().load(request.json)

    if user_auth_schema:
        try:
            user_auth = db.session.query(UserAuth).filter(UserAuth.token==user_auth_schema["token"]).first()
        except:
            return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error
    
        if not user_auth:
            return jsonify({"error": "No logged in user found with token {}".format(user_auth_schema["token"])}), HTTP.bad_request
        else:
            return jsonify({"message": "Hello, {}!".format(user_auth.username),
                            "version": app_version,
                            "authenticated": True}), HTTP.ok
    else:
        return jsonify({"message": "Hello, server!",
                        "version": app_version,
                        "authenticated": False}), HTTP.ok

@app.route("/register", methods=['POST'])
def register_user():
    """
    Registers an user in the database
    """
    try:
        user_schema = UserSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), HTTP.bad_request

    user = User(
        username=user_schema["username"],
        password=user_schema["password"],
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        return jsonify({"error": "This username is already in use"}), HTTP.bad_request
    except:
        db.session.rollback()
        return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error

    return jsonify({"username": user.username}), HTTP.created

@app.route("/login", methods=['GET', 'POST'])
def login_user():
    """
    If request is GET: Fetches the user token, if any
    If request is POST: Creates a login token
    """
    try:
        user_schema = UserSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), HTTP.bad_request

    try:
        user = db.session.get(User, user_schema["username"])
    except:
        return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error
    else:
        if not user:
            return jsonify({"error": "User {} not found".format(user_schema["username"])}), HTTP.bad_request

    # This is obviously not a good practice, but the purpose of this
    # project is not to be secure, just to demonstrate an auth API
    if user.password != user_schema["password"]:
        return jsonify({"error": "Invalid username or password"}), HTTP.bad_request

    if request.method == "GET":
        try:
            user_auth = db.session.get(UserAuth, user_schema["username"])
        except:
            return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error
        else:
            if request.method == "GET" and not user:
                    return jsonify({"error": "User {} is not logged in".format(user_schema["username"])}), HTTP.bad_request
            elif request.method == "POST" and user:
                    return jsonify({"error": "User {} is already logged in".format(user_schema["username"])}), HTTP.bad_request

    if request.method == "GET":
        return jsonify({"username": user_auth.username,
                        "token": user_auth.token}), HTTP.ok
    elif request.method == "POST":
        user_auth = UserAuth(username=user_schema["username"])
        try:
            db.session.add(user_auth)
            db.session.commit()
        except:
            db.session.rollback()
            return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error

        return jsonify({"username": user_auth.username,
                        "token": user_auth.token}), HTTP.created

@app.route("/logout", methods=['DELETE'])
def logout_user():
    """
    Deletes an user token
    """
    try:
        user_auth_schema = UserAuthSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), HTTP.bad_request

    try:
        user_auth = db.session.query(UserAuth).filter(UserAuth.token==user_auth_schema["token"]).first()
    except:
        return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error
    
    if not user_auth:
        return jsonify({"error": "No logged in user found with token {}".format(user_auth_schema["token"])}), HTTP.bad_request

    try:
        db.session.delete(user_auth)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"error": "Something went wrong with the server"}), HTTP.internal_server_error

    return jsonify({"expired_token": user_auth.token}), HTTP.ok

if __name__ == "__main__":
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.run()
