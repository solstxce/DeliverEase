from werkzeug.security import generate_password_hash

passwords = {
    'admin': 'admin123',
    'user': 'user123',
    'driver': 'driver123'
}

for user, password in passwords.items():
    hash = generate_password_hash(password)
    print(f"{user}: {hash}") 