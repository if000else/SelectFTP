import os, time, uuid, socket, select
import threading

ip, port = 'localhost', 1212


class client_ftp():
    '''
    ftp server class
    '''

    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect((ip,port))
        self.lock = threading.Lock()

    def put(self,comm):
        import json
        os.chdir('./Dlowload')
        filename = comm.split()[1]
        size = os.stat(filename).st_size
        data = json.dumps([filename,size,0])
        send_size = 0
        self.sock.send(data.encode()) # send [name,size,state]

        with self.lock: # a file can be use at the a time
            with open(filename,'rb') as f:
                f.seek(send_size)
                for line in f:
                    self.sock.send(line)
            print("sending done!")



    def get(self,comm):
        import json
        os.chdir('./Dlowload')
        data = self.sock.recv(1024).decode()
        file_info = json.loads(data)  # [name,size,state]
        to_size = file_info[1]
        recv_size = 0
        filename = uuid.uuid1()
        with self.lock:
            with open('./%s'%filename,'ab'):
                while recv_size < to_size:
                    size = to_size - recv_size
                    if size < 1024:
                        self.sock.recv(size)
                    else:
                        self.sock.recv(1024)
                else:
                    print("get file done!")

    def run(self):
        while True:
            inp = input("command>>:").strip()
            if inp:
                command = inp.split()
                if command[0] == 'put':
                    if os.path.exists('./Upload/%s'%command[1]):
                        self.sock.send(inp.encode())
                        put = threading.Thread(target=self.put,args=(command,))
                        put.start()
                        put.join()
                    else:
                        print("file does not exist!")
                elif command[0] == 'get':
                    if os.path.exists('./Download/%s'%command[1]):
                        self.sock.send(inp.encode())
                        get = threading.Thread(target=self.get, args=(command,))
                        get.start()
                        get.join()
                    print("file does not exist!")

                else:
                    print("invalid command!")
            else:
                pass