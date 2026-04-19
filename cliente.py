
import socket

# ----- Config de conexion ------
HOST = "localhost"
PORT = 5000


def main():
    print("=" * 40)
    print("   Chat - cliente  ")
    #la consigna decia 'exito' pero asumo que quiso decir 'exit' que seria mas logico
    print("  'exit' para salir.")
    print("=" * 40)

    # Crear el socket TCP del cliente
    # AF_INET -> IPv4 | SOCK_STREAM -> TCP
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conectarse al servidor
        cliente.connect((HOST, PORT))
        print(f"[CLIENTE] conectado a {HOST}:{PORT}\n")

        # ─── Bucle de envío de mensajes ───────────────────────────────────────
        while True:
            mensaje = input("Vos: ").strip()

            # Condicion de salida: el usuario escribe 'exit'
            if mensaje.lower() == "exit":
                print("[CLIENTE] Cerrando conexión. ¡Hasta luego!")
                break

            # No enviar mensajes vacios
            if not mensaje:
                print("[CLIENTE] El mensaje no puede estar vacío.")
                continue

            # Enviar el mensaje al servidor (codificado en UTF-8)
            cliente.sendall(mensaje.encode("utf-8"))

            # Esperar y mostrar la respuesta del servidor
            respuesta = cliente.recv(1024).decode("utf-8")
            print(f"Servidor: {respuesta}\n")

    except ConnectionRefusedError:
        # El servidor no está corriendo o la dirección/puerto son incorrectos
        print(f"[ERROR] No se pudo conectar a {HOST}:{PORT}.")
        print("        Asegurate de que el servidor esté corriendo primero.")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
