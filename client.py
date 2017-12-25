import os, time, uuid, socket, select

ip, port = 'localhost', 1212


class client_ftp():
    '''
    ftp server class
    '''

    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect((ip,port))

    def put(self,comm):
        import json
        os.chdir('./Dlowload')
        filename = comm.split()[0]
        size = os.stat(filename).st_size
        data = json.dumps([filename,size,0])
        send_size = 0
        self.sock.send(data.encode()) # send [name,size,state]
        with open(filename,'rb') as f:
            f.seek(send_size)
            for line in f:
                self.sock.send(line)



    def get(self,comm):
        os.chdir('./Dlowload')
    def run(self):
        while True:
            inp = input("command>>:").strip()
            if inp:
                command = inp.split()
                self.sock.send(inp.encode())
                if command[0] == 'put':
                    self.put(command)
                elif command[0] == 'get':
                    self.get(command)
                else:
                    data = self.sock.recv(1024)
                    print(data)
                    print("invalid command!")
            else:
                pass