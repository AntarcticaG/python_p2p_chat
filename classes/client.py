from errno import EBADF

import classes.server_client_base as scb 
import threading
import socket
import os


class Client(scb.ServerClientBase):

    FILE_MESSAGE_TYPE = 4

    def __init__(self, host_ip, port):
        super().__init__()

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.settimeout(5)
        self._s.connect((host_ip, port))
        self._s.settimeout(None)

        th = threading.Thread(target=self.recv_handler, kwargs={'sock':self._s})
        th.start()

    def recv_handler(self, sock):
        while True:
            try:
                msg = sock.recv(1024)
                msg = msg.decode()
                if not msg:
                    self.show_sys_msg("Host is disconnected")
                    self.destroy()
                    break

                if msg.startswith("/file "):
                    filename = msg[len("/file "):] 
                    self.save_received_file(filename)
                else:
                    self._msg_queue.put(msg)
            except Exception as e:
                if isinstance(e, OSError) and e.errno == EBADF: 
                    # User closed the program
                    break

                self.show_sys_msg(repr(e))

    def send_msg(self, msg):
        msg_type = self.determine_msg_type(msg)

        try:
            if self._s is not None:
                if msg_type == self.FILE_MESSAGE_TYPE:
                    self.send_file(msg) 
                else:
                    self._s.send(msg.encode('utf-8'))  # Отправка текстового сообщения
            else:
                print("Error: Socket not available.")
        except Exception as e:
            print("Error sending message:", e)

    def save_received_file(self, filename, file_data):
        try:
            # Путь для сохранения файла
            print(filename)
            save_path = os.path.join("received_files", filename)

            # Создаем директорию для сохранения файла, если её нет
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Сохраняем файл
            with open(save_path, "wb") as file:
                file.write(file_data)

            print(f"File '{filename}' saved successfully.")
        except Exception as e:
            print(f"Error saving file '{filename}': {e}")

    def send_file(self, file_path):
        try:
            filename_msg = "/file " + os.path.basename(file_path)
            self._s.send(filename_msg.encode('utf-8'))
            with open(file_path, "rb") as file:
                file_data = file.read()
                self._s.sendall(file_data)
        except Exception as e:
            print("Error sending file:", e)
    
    def show_sys_msg(self, msg):
        if not msg:
            return

        msg = "SYSTEM: " + msg + "."
        self._msg_queue.put(msg)

    def destroy(self):
        if self._s is not None:
            self._s.close()
            self._s = None

    def determine_msg_type(self, msg):
        if not msg:
            return 1

        if len(msg) >= 5 and msg[:4] == "/nc ":
            return 2

        return 3
