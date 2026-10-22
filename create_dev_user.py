
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.user import User


app = create_app()


with app.app_context():
    email = input("Development user email: ").strip().lower()

    if not email:
        raise SystemExit("Email cannot be empty.")

    # Avoid creating a duplicate user.
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print(f"User already exists. User ID: {existing_user.id}")
        raise SystemExit(0)

    password = getpass("Development password (hidden): ")

    if len(password) < 12:
        raise SystemExit("Use a password with at least 12 characters.")

    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        raise SystemExit("Passwords do not match.")

    user = User(
        email=email,
        password_hash=generate_password_hash(password)
    )

    try:
        db.session.add(user)
        db.session.commit()

        print("Development user created successfully.")
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
    except Exception:
        db.session.rollback()
        raise
