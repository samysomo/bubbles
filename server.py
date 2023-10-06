
#Codigo del sercidor

import socket
import threading
import json
import time
import base64

# Configura el servidor
HOST = 'localhost'
PORT = 8090

# Lista para almacenar los clientes
clientes = []
nombres_clientes = []

# Función para manejar conexiones de clientes
def manejar_cliente(cliente_socket):
    try:
        nombre = cliente_socket.recv(1024).decode('utf-8')
        nombre = nombre.strip()  # Elimina espacios en blanco al principio y al final del nombre
        nombres_clientes.append(nombre)

        mensaje_bienvenida = f"{nombre} se ha unido al chat!"
        mensaje_bienvenida = "MENSAJEGRUPAL:" + mensaje_bienvenida
        broadcast(mensaje_bienvenida)
        print(mensaje_bienvenida)
        
        while True:
            #Recibir los mensajes del cliente, 1024 es la cantidad maxima de bytes que se recibiran a la vez, .decode transforma esos bytes a cadenas de texto
            mensaje = cliente_socket.recv(1024).decode('utf-8')
            if mensaje.startswith("DESCONECTAR:"):
                nombre_cliente = mensaje[13:]

                #Eliminar el nombre del cliente desconectado de la lista que se manda al usuario
                nombres_clientes.remove(nombre_cliente)
                mensaje_despedida = f"{nombre} se ha desconectado."
                mensaje_despedida = "MENSAJEGRUPAL:" + mensaje_despedida
                broadcast(mensaje_despedida)

                #Eliminar el hilo del cliente desconectado
                clientes.remove(cliente_socket)  
                break

            elif mensaje.startswith("NOTIFICACIONCHATPRIVADO:"):
                mensaje = mensaje[24:]
                mensaje_json = json.loads(mensaje)
                nombre_destinatario = mensaje_json["destinatario"]
                notificacion_cp = mensaje_json["mensaje"]
                notificacion_cp = "MENSAJEGRUPAL:" + notificacion_cp
                indice_destinatario = nombres_clientes.index(nombre_destinatario)
                socket_destinatario = clientes[indice_destinatario]
                socket_destinatario.send(notificacion_cp.encode('utf-8'))

            elif mensaje.startswith("MENSAJEPRIVADO:"):
                mensaje = mensaje[15:]
                mensaje_json = json.loads(mensaje)
                nombre_destinatario = mensaje_json["destinatario"]
                mensaje_privado = mensaje_json["mensaje"]
                mensaje_con_nombre = f"{nombre}: {mensaje_privado}"
                print(mensaje_privado)
                indice_destinatario = nombres_clientes.index(nombre_destinatario)
                socket_destinatario = clientes[indice_destinatario]
                mensaje_json = {
                    "remitente" : nombre,
                    "mensaje" : mensaje_con_nombre
                }
                mensaje_json = json.dumps(mensaje_json)
                socket_destinatario.send(("MENSAJEPRIVADO:" + mensaje_json).encode('utf-8'))

            elif mensaje.startswith("ENVIARARCHIVO:"):
                mensaje = mensaje[14:]
                mensaje_json = json.loads(mensaje)
                nombre_destinatario = mensaje_json["destinatario"]
                archivos_info = mensaje_json["archivos"]  # Cambiar "archivo" a "archivos"
                indice_destinatario = nombres_clientes.index(nombre_destinatario)
                socket_destinatario = clientes[indice_destinatario]

                for archivo in archivos_info:
                    nombre_archivo = archivo["nombre"]
                    contenido_archivo = archivo["contenido"].encode('latin1')  # Codificar el contenido como bytes

                    mensaje_json = {
                        "remitente": nombre,
                        "archivo": {
                            "nombre": nombre_archivo,
                            "contenido": contenido_archivo.decode('latin1')  # Decodificar el contenido binario a una cadena
                        },
                        "mensaje": f"{nombre}: te ha enviado un archivo!"
                    }
                    mensaje_json = json.dumps(mensaje_json)
                    socket_destinatario.send(("MENSAJEPRIVADO:" + mensaje_json).encode('utf-8'))
            
            elif mensaje.startswith("MENSAJEGRUPAL:"):    
                mensaje_con_nombre = f"{nombre}: {mensaje[14:]}"
           
                for cliente in clientes:
                    if cliente != cliente_socket:
                        try:
                            cliente.send(("MENSAJEGRUPAL:" + mensaje_con_nombre).encode('utf-8'))
                        except:
                            continue
    except:
        clientes.remove(cliente_socket)
     

# Función para enviar un mensaje a todos los clientes
def broadcast(mensaje):
    for cliente in clientes:
        #if cliente != remitente:
            try:
                cliente.send(mensaje.encode('utf-8'))
            except:
                continue

#Función para mandar los usuarios periodicamente
def enviar_lista_clientes():
    while True:
        lista_nombres = {
            "usuarios" : nombres_clientes
        }
        usuarios = json.dumps(lista_nombres)
        etiqueta = "usuarios:"+ usuarios
        broadcast(etiqueta)

        time.sleep(10)





# Configura el servidor y espera conexiones
    #AF_INET - Especificar protocolo IPV4, SOCK_STREAM - Espercificar que será un socket TCP
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Enlazar una direccion y puerto al servidor
servidor.bind((HOST, PORT))
    #Comenzar a escuchar conexiones entrantes, se pasa como parametro el numero maximo de conexiones permitidas
servidor.listen(5)
print(f"Servidor escuchando en {HOST}:{PORT}")

while True:
    #Cuando un cliente se conecta, accept() devuelve un nuevo objeto de socket llamado cliente y este se guarda en la lista de clientes
    cliente, direccion = servidor.accept()
    clientes.append(cliente)

    #Crear un hilo que manda llamar la funcion de manejar cliente para ese cliente en especifico
    cliente_thread = threading.Thread(target=manejar_cliente, args=(cliente,))
    cliente_thread.start()

    #Crear un hilo que se ejecute en segundo plano para mandar la lista de usuarios conectados
    enviar_lista = threading.Thread(target=enviar_lista_clientes)
    enviar_lista.daemon = True
    enviar_lista.start()
