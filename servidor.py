
import socket
import sqlite3
import datetime
import threading

# ----- Config general ------
HOST = "localhost"
PORT = 5000
DB_PATH = "mensajes.db"


# ----- Inicializacion de la db -----
def inicializar_db():

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                contenido   TEXT    NOT NULL,
                fecha_envio TEXT    NOT NULL,
                ip_cliente  TEXT    NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("[DB] Base de datos inicializada correctamente.")
    except sqlite3.Error as e:
        # Error crítico: sin DB no tiene sentido continuar
        raise RuntimeError(f"[DB] No se pudo inicializar la base de datos: {e}")


# ─── Almacenamiento de mensajes ────────────────────────────────────────────────
def guardar_mensaje(contenido: str, ip_cliente: str) -> str:
    """
    Inserta un mensaje en la tabla 'mensajes' y devuelve el timestamp.

    Args:
        contenido  : texto del mensaje recibido
        ip_cliente : IP del cliente que envió el mensaje

    Returns:
        timestamp  : string con la fecha/hora de recepción (ISO 8601).
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mensajes (contenido, fecha_envio, ip_cliente) VALUES (?, ?, ?)",
            (contenido, timestamp, ip_cliente),
        )
        conn.commit()
        conn.close()
        print(f"[DB] Guardado — ip: {ip_cliente} | fecha: {timestamp} | msg: '{contenido}'")
    except sqlite3.Error as e:
        print(f"[DB] Error al guardar el mensaje: {e}")
    return timestamp


# ----- Manejo de cada cliente en su propio hilo ------
def manejar_cliente(conn_cliente: socket.socket, addr: tuple):
    """
    Atiende a un cliente mientras este envíe mensajes.
    Cada mensaje se almacena en la DB y recibe una confirmación con timestamp.

    Args:
        conn_cliente : socket de la conexión aceptada.
        addr         : tupla (ip, puerto) del cliente.
    """
    ip_cliente = addr[0]
    print(f"[SERVIDOR] Conexión aceptada desde {ip_cliente}:{addr[1]}")

    try:
        while True:
            # Recibir datos del cliente (hasta 1024 bytes)
            datos = conn_cliente.recv(1024)

            # Si recv devuelve bytes vacíos, el cliente cerró la conexión
            if not datos:
                print(f"[SERVIDOR] Cliente {ip_cliente} desconectado.")
                break

            mensaje = datos.decode("utf-8").strip()
            print(f"[SERVIDOR] Mensaje recibido de {ip_cliente}: '{mensaje}'")

            # Guardar en DB y obtener el timestamp
            timestamp = guardar_mensaje(mensaje, ip_cliente)

            # Responder al cliente con la confirmacion solicitada por el enunciado
            respuesta = f"Mensaje recibido: {timestamp}"
            conn_cliente.sendall(respuesta.encode("utf-8"))

    except ConnectionResetError:
        # El cliente cerro la conexión abruptamente
        print(f"[SERVIDOR] Conexión con {ip_cliente} interrumpida.")
    except Exception as e:
        print(f"[SERVIDOR] Error inesperado con {ip_cliente}: {e}")
    finally:
        conn_cliente.close()


# ---- Inicialización y arranque del socket TCP/IP -----
def inicializar_socket() -> socket.socket:
    """
    Crea y configura el socket del servidor TCP.

    Returns:
        sock : socket listo para hacer bind y listen.
    """
    # AF_INET   → protocolo IPv4
    # SOCK_STREAM → TCP (orientado a conexin)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_REUSEADDR permite reutilizar el puerto inmediatamente después de reiniciar el servidor, evitando el error "Address already in use" en reinicios rápidos.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    return sock


# ---- Aceptación de conexiones -----
def aceptar_conexiones(servidor: socket.socket):
    """
    Bucle principal: espera clientes y lanza un hilo por cada conexión aceptada.
    Permite atender múltiples clientes de forma concurrente.

    Args:
        servidor : socket del servidor ya en modo escucha.
    """
    print(f"[SERVIDOR] Escuchando en {HOST}:{PORT} — esperando clientes...\n")
    while True:
        try:
            conn_cliente, addr = servidor.accept()
            # Cada cliente se maneja en un hilo independiente para no bloquear
            hilo = threading.Thread(
                target=manejar_cliente,
                args=(conn_cliente, addr),
                daemon=True,   # El hilo se cierra automáticamente si el proceso termina
            )
            hilo.start()
        except OSError:
            # Ocurre cuando el socket del servidor se cierra (ej. Ctrl+C)
            break


# ─── Punto de entrada ─────────────────────────────────────────────────────────
def main():
    # 1. Preparar la base de datos
    inicializar_db()

    # 2. Crear el socket TCP
    servidor = inicializar_socket()

    try:
    # 3. Asociar el socket a la dirección y puerto configurados
        servidor.bind((HOST, PORT))

        # 4. Poner el socket en modo escucha (cola de hasta 5 conexiones pendientes)
        servidor.listen(5)

        # 5. comenzar a aceptar clientes
        aceptar_conexiones(servidor)

    except OSError as e:
        # Error habitual: puerto ya ocupado por otro proceso
        print(f"[ERROR] No se pudo iniciar el servidor: {e}")
        print(f"        Verificá que el puerto {PORT} no esté en uso.")
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Apagando servidor...")
    finally:
        servidor.close()
        print("[SERVIDOR] Socket cerrado. Hasta la próxima.")


if __name__ == "__main__":
    main()
