from errno import EBADF

import classes.server_client_base as scb 
import threading
import socket


class Client(scb.ServerClientBase):

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
                msg_type = self.determine_msg_type(msg)

                if msg_type == self.FILE_MESSAGE_TYPE:
                    # Получаем файл
                    file_data = sock.recv(1024)
                    file_path = os.path.join(os.getcwd(), 'received_file.txt')
                    with open(file_path, 'wb') as file:
                        file.write(file_data)
                    self.show_sys_msg("File received and saved as 'received_file.txt'")
                else:
                    self._msg_queue.put(msg)
            except Exception as e:
                if e.errno == EBADF: 
                    # User closed the program
                    break
                self.show_sys_msg(repr(e))

    def send_msg(self, msg):
        if not msg:
            return

        try:
            if self._s is not None:
                self._s.sendall(msg.encode())
            else:
                self._msg_queue.put(msg)
        except Exception as e:
            self.show_sys_msg(repr(e))

    def send_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                self.send_msg(str(self.FILE_MESSAGE_TYPE))
                self.send_msg(file_data)
        except Exception as e:
            self.show_sys_msg(repr(e))
    
    def show_sys_msg(self, msg):
        if not msg:
            return

        msg = "SYSTEM: " + msg + "."
        self._msg_queue.put(msg)

    def destroy(self):
        if self._s is not None:
            self._s.close()
            self._s = None
