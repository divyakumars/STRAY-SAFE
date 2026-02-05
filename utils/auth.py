# utils/auth.py - FIXED VERSION

from utils import storage
import base64


def ensure_admin_exists():
    """Ensure default admin account exists in database"""
    users = storage.read("users", [])

    # Check if admin already exists
    admin_exists = any(u.get("email") == "admin@rescuepaws.ai" for u in users)

    if not admin_exists:
        # Add default admin to database
        users.append({
            "email": "admin@rescuepaws.ai",
            "name": "Admin",
            "password": "admin123",
            "role": "admin",
            "phone": "+919840277042",
            "profile_picture": None,
            "active": True,
            "created_at": str(__import__('datetime').datetime.now())
        })
        storage.write("users", users)


def login(email, password):
    # Ensure admin exists in database before login
    ensure_admin_exists()

    users = storage.read("users", [])

    # Check all users (including the admin we just ensured exists)
    for user in users:
        if user.get("email") == email and user.get("password") == password:
            return True, "Login successful", user

    return False, "Invalid credentials", None


def register(email, name, password, role="user", phone="", profile_picture=None):
    users = storage.read("users", [])
    if any(u.get("email") == email for u in users):
        return False, "Email already registered"

    users.append({
        "email": email,
        "name": name,
        "password": password,
        "role": role,
        "phone": phone,
        "profile_picture": profile_picture,
        "active": True,
        "created_at": str(__import__('datetime').datetime.now())
    })

    storage.write("users", users)
    return True, "Account created successfully"