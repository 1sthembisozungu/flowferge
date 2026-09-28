from flask import Blueprint 

#Blueprint is the way to organize you flask app into smaller, reusable components, it helps keep large projects modular

from app import db
from app.models.user import User

test = Blueprint("test", __name__)

# blueprint object
# "test" is the blueprint's name used when registering it with the main app
#__name__ tells Flask where this blueprint is defined

@test.route("/api/health")
def health():

    return {
        "status": "ok",
        "services": "FlowForge API"
    }
    # Returns a Python dictionary
    # Flask automatically converts this dictionary into a JSON response.


@test.route("/api/users")
def users():

    users = User.query.all()

    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }

            for user in users

        ]
    }
