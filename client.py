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
        '''
        send file info ,then send file date
        :param comm:
        :return:
        '''
        import pickle
        os.chdir('./Download')  # client dir
        filename = comm.split()[1]
        size = os.stat(filename).st_size
        data = pickle.dumps([filename,size,0])
        # send_size = 0
        self.sock.send(data) # send [name,size,state]

        with self.lock: # a file can be use at the a time
            with open(filename,'rb') as f:
                # f.seek(send_size)
                for line in f:
                    self.sock.send(line)
            print("sending done!")



    def get(self,comm):
        import pickle
        self.sock.send(comm.encode())
        os.chdir('./Download')  # client dir
        data = self.sock.recv(1024)
        # print("file info:", data,type(data))
        # data = data.decode()

        file_info = pickle.loads(data)  # [name,size,state]

        total_size = file_info[1] # total size
        recv_size = 0
        filename = str(uuid.uuid1()).replace('-','')
        with open('./%s'%filename,'wb'):
            while recv_size < total_size:
                size = total_size - recv_size
                if size > 1024:
                    data = self.sock.recv(1024)
                else:
                    data = self.sock.recv(size)
                recv_size += len(data)
            else:
                print("get file done!")

    def run(self):
        while True:
            inp = input("command>>:").strip()
            if inp:
                command = inp.split()
                if command[0] == 'put': # put file to server
                    if os.path.exists('./Download/%s'%command[1]):
                        self.sock.send(inp.encode())
                        put = threading.Thread(target=self.put, args=(command,))
                        put.start()
                        put.join()

                    else:
                        print("file does not exist!")

                elif command[0] == 'get':
                    if os.path.exists('./Upload/%s'%command[1]):
                        self.get(inp)
                        # get = threading.Thread(target=self.get, args=(command,))
                        # get.start()
                        # get.join()

                    else:# file does not exist in server
                        print("file does not exist in server")


                else:
                    print("invalid command!")
            else:
                pass

if __name__ == '__main__':
    client = client_ftp()
    client.run()