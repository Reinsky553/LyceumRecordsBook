from werkzeug.security import generate_password_hash
inp = input("Введите пароль для генерации хеша: ")
print(generate_password_hash(inp))
