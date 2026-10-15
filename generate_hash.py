import bcrypt

plain_password = "Admin2026!"
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)

print(hashed_password.decode('utf-8'))