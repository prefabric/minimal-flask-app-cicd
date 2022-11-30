from flask import (
    Blueprint,
    render_template,
)
from flask_app.models import User


bp = Blueprint("index", __name__)


@bp.route("/", methods=["GET"])
def index():
    User.query.order_by(User.email).all()
    return render_template("index.html")


@bp.route("/ping", methods=["GET"])
def ping():
    return render_template("index.html")
