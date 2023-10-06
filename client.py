
#Codigo del cliente

import socket
import threading
import tkinter as tk
from tkinter import simpledialog
from tkinter import Listbox
from tkinter import filedialog
import json
import base64
import os

# Configura el cliente
HOST = 'localhost'
PORT = 8090

RUTA = "C:\\Users\\samys\\OneDrive\\Escritorio\\pruebaFTP\\"

# Crear un diccionario para almacenar las ventanas de chat privado
ventanas_privadas = {}
interfaz_privada_e = True

# Función para enviar mensajes al servidor
def enviar_mensaje():
    mensaje = mensaje_var.get()
    #Vaciar la barra de mensajes cunando se manda uno
    mensaje_var.set("")
    if mensaje:
        mensaje_con_nombre = f"Tú: {mensaje}"
        mensajes_text.config(state=tk.NORMAL)
        mensajes_text.insert(tk.END, mensaje_con_nombre + '\n', 'mensaje_enviado')
        mensajes_text.tag_add('mensaje_enviado', 'end-2l', 'end-1l')
        mensajes_text.config(state=tk.DISABLED)
        cliente_socket.send(("MENSAJEGRUPAL:" + mensaje).encode('utf-8'))

# Función para recibir mensajes del servidor
def recibir_mensajes():
    while True:
        try:
            mensaje = cliente_socket.recv(1024).decode('utf-8')
            
            if mensaje.startswith("usuarios:"):
                actualizar_lista_usuarios(mensaje)
                
            elif mensaje.startswith("MENSAJEGRUPAL:"):
                # Mostrar otros mensajes en el cuadro de mensajes principal
                mensaje_con_nombre = mensaje[14:]
                mensajes_text.config(state=tk.NORMAL)
                mensajes_text.insert(tk.END, mensaje_con_nombre + '\n', 'mensaje_recibido')
                mensajes_text.tag_add('mensaje_recibido', 'end-2l', 'end-1l')
                mensajes_text.config(state=tk.DISABLED)
            
            elif mensaje.startswith("MENSAJEPRIVADO:"):
                mensaje_json = json.loads(mensaje[15:])  # Elimina la etiqueta "MENSAJEPRIVADO:"
                remitente = mensaje_json["remitente"]

                if "archivo" in mensaje_json:
                    print("LLego un archivo")
                    archivo_info = mensaje_json["archivo"]
                    nombre_archivo = archivo_info["nombre"]
                    contenido_archivo = archivo_info["contenido"].encode('latin1')  # Codificar el contenido como bytes

                    ruta_destino = RUTA + nombre_archivo
                    # Guardar el archivo recibido en el sistema
                    with open(ruta_destino, "wb") as file:
                        file.write(contenido_archivo)
                    mensaje_texto = mensaje_json["mensaje"]

                else:
                    mensaje_texto = mensaje_json["mensaje"]

                print(mensaje_texto) 

                if remitente not in ventanas_privadas:
                    text_box = crear_ventana_chat_privado(remitente)
                else:
                    text_box = ventanas_privadas[remitente]["chatbox"]

                #Agrega el mensaje al cuadro de texto del chat privado
                text_box.config(state=tk.NORMAL)
                text_box.insert(tk.END, f"{mensaje_texto}\n", 'mensaje_recibido')
                text_box.config(state=tk.DISABLED)
                
        except:
            break

#Solicitar el nombre del usuario mediante un cuadro de dialogo
def solicitar_nombre():
    global nombre 
    nombre = simpledialog.askstring("Nombre", "Ingresa tu nombre:")
    cliente_socket.send(nombre.encode('utf-8'))


# Mostrar y actualizar la lista de usuarios en la interfaz
def actualizar_lista_usuarios(lista):
    lista_clientes_frame.delete(0, tk.END)  # Borrar la lista actual de clientes    
    # Procesar la lista de nombres de usuarios
    lista_nombres = json.loads(lista[9:])  # Elimina la etiqueta "usuarios:"

    # Actualizar la lista de clientes
    for nom in lista_nombres['usuarios']:
        if nom != nombre:
            lista_clientes_frame.insert(tk.END, nom)


def desconectar_usuario():
    mensaje = f"DESCONECTAR: {nombre}"
    print(nombre)
    cliente_socket.send(mensaje.encode('utf-8'))
    
    cliente_socket.close()
    root.quit()
    root.destroy()

#Función para manejar clics en chats privados
def abrir_chat_privado(event):
    # Obtener el índice del elemento clicado
    seleccion = lista_clientes_frame.curselection()
    if seleccion:
        indice = seleccion[0]
        usuario_seleccionado = lista_clientes_frame.get(indice)
        # Aquí puedes abrir una ventana de chat privado para 'usuario_seleccionado'
        crear_ventana_chat_privado(usuario_seleccionado)
        notificacion = f"{nombre} ha abierto un chat privado contigo!"
        notificacion_json = {
            "remitente" : nombre,
            "destinatario" : usuario_seleccionado,
            "mensaje" : notificacion
        }
        notificacion_json = json.dumps(notificacion_json)
        notificacion_json = "NOTIFICACIONCHATPRIVADO:"+ notificacion_json
        cliente_socket.send(notificacion_json.encode('utf-8'))


# Crear una ventana de chat privado
def crear_ventana_chat_privado(nombre_usuario):
    ventana_chat_privado = tk.Toplevel(root)
    ventana_chat_privado.title(f"Chat privado con {nombre_usuario}")

    # Crear una Textbox para mostrar los mensajes
    chat_textbox = tk.Text(ventana_chat_privado, state=tk.DISABLED)
    chat_textbox.pack(fill=tk.BOTH, expand=True)

    # Crear una Entry para escribir mensajes
    mensaje_var = tk.StringVar()
    mensaje_entry = tk.Entry(ventana_chat_privado, textvariable=mensaje_var)
    mensaje_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Botón para enviar mensajes
    enviar_button = tk.Button(ventana_chat_privado, text="Enviar Archivo", command=lambda: enviar_archivo())
    enviar_button.pack(side=tk.RIGHT)

    #Enviar el mensaje cuando se presiona enter
    mensaje_entry.bind("<Return>", lambda event=None: enviar_mensaje_privado())

    # Configura etiquetas para mensajes enviados y recibidos
    chat_textbox.tag_configure('mensaje_enviado', justify='right', background='lightblue')
    chat_textbox.tag_configure('mensaje_recibido', justify='left', background='lightgreen')
    
    # Función para enviar mensajes privados
    def enviar_mensaje_privado():
        mensaje = mensaje_var.get()
        if mensaje:
            mensaje_con_nombre = f"Tú: {mensaje}"
            chat_textbox.config(state=tk.NORMAL)
            chat_textbox.insert(tk.END, mensaje_con_nombre + '\n', 'mensaje_enviado')
            mensajes_text.tag_add('mensaje_enviado', 'end-2l', 'end-1l')
            chat_textbox.config(state=tk.DISABLED)
            mensaje_completo = {
                "destinatario" : nombre_usuario,
                "mensaje" : mensaje
            }
            mensaje_completo = json.dumps(mensaje_completo)
            cliente_socket.send(("MENSAJEPRIVADO:" + mensaje_completo).encode('utf-8'))

            # Aquí debes enviar el mensaje al otro cliente en el chat privado
            mensaje_var.set("")
    
    def enviar_archivo():
        archivos = filedialog.askopenfilenames()
        if archivos:
            contenido_archivos = []
            for archivo in archivos:
                with open(archivo, "rb") as file:
                    archivo_contenido = file.read()
                    contenido_archivos.append(archivo_contenido)

            archivos_info = []
            for archivo, contenido in zip(archivos, contenido_archivos):
                nombre_archivo = archivo.split("/")[-1]  # Obtener el nombre del archivo sin la ruta completa
                archivo_info = {
                    "nombre": nombre_archivo,
                    "contenido": contenido.decode('latin1')  # Decodificar el contenido binario a una cadena
                }
                archivos_info.append(archivo_info)

            mensaje_completo = {
                "destinatario": nombre_usuario,
                "archivos": archivos_info  # Cambiar "archivo" a "archivos" para enviar la lista de archivos
            }
            mensaje_completo = json.dumps(mensaje_completo)
            cliente_socket.send(("ENVIARARCHIVO:" + mensaje_completo).encode('utf-8'))

        
    ventanas_privadas[nombre_usuario] = {
        "ventana" : ventana_chat_privado,
        "chatbox" : chat_textbox
    }
    return chat_textbox
        
    
#Crear el socket para la conexion con el servidor y conectarse
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente_socket.connect((HOST, PORT))

# Configura la interfaz gráfica
root = tk.Tk()
root.title("Chat Grupal")

mensaje_var = tk.StringVar()
mensaje_entry = tk.Entry(root, textvariable=mensaje_var)
mensaje_entry.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=10, pady=10)

#Enviar el mensaje cuando se presiona enter
mensaje_entry.bind("<Return>", lambda event=None: enviar_mensaje())

mensajes_text = tk.Text(root, state=tk.DISABLED)
mensajes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

#Frame de la lista de usuarios
lista_clientes_frame = tk.Listbox(root)
lista_clientes_frame.pack(side=tk.LEFT, before=mensajes_text ,fill=tk.BOTH, padx=10, pady=10)

# Asignar la función de manejo de clics al Listbox
lista_clientes_frame.bind("<Double-Button-1>", abrir_chat_privado)


# Configura etiquetas para mensajes enviados y recibidos
mensajes_text.tag_configure('mensaje_enviado', justify='right', background='lightblue')
mensajes_text.tag_configure('mensaje_recibido', justify='left', background='lightgreen')


# Llama a la función solicitar_nombre para obtener el nombre del usuario
solicitar_nombre()

# Configurar el evento de cierre de la ventana
root.protocol("WM_DELETE_WINDOW", desconectar_usuario)

# Recibir y mostrar el mensaje de bienvenida del servidor
mensaje_bienvenida = cliente_socket.recv(1024).decode('utf-8')

# Inicia un hilo para recibir mensajes del servidor
recibir_thread = threading.Thread(target=recibir_mensajes)
recibir_thread.start()


root.mainloop()