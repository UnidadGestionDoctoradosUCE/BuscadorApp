"""
Utilidad CLI para agregar o actualizar usuarios con contraseña cifrada en SHA-256
dentro de data/usuarios.json sin re-hashear los usuarios existentes.
Uso: python data/cifrador.py
"""
import getpass
import hashlib
import json
import os


def hash_sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def main():
    ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.json")
    if os.path.exists(ruta_json):
        with open(ruta_json, "r", encoding="utf-8") as f:
            usuarios = json.load(f)
    else:
        usuarios = []

    print("=== Gestión de Usuarios - BuscadorApp ===")
    nombre = input("Nombre completo para mostrar (ej. Dra. María Pérez): ").strip()
    usuario = input("Nombre de usuario (login): ").strip()
    contrasena = getpass.getpass("Contraseña: ").strip()

    if not nombre or not usuario or not contrasena:
        print("[ERROR] Todos los campos son obligatorios.")
        return

    user_hash = hash_sha256(usuario)
    pass_hash = hash_sha256(contrasena)

    actualizado = False
    for entry in usuarios:
        if entry.get("usuario") == user_hash:
            entry["nombre"] = nombre
            entry["contrasena"] = pass_hash
            actualizado = True
            break

    if not actualizado:
        usuarios.append({
            "usuario": user_hash,
            "contrasena": pass_hash,
            "nombre": nombre,
        })

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

    accion = "actualizado" if actualizado else "registrado"
    print(f"[OK] Usuario '{nombre}' {accion} correctamente en {ruta_json}.")


if __name__ == "__main__":
    main()
