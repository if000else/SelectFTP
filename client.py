import os, time, uuid, socket, select
import threading

ip, port = 'localhost', 8888


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
        # os.chdir('./Download')  # client dir
        self.sock.send(comm.encode())
        filename = comm.split()[1]
        size = os.stat("Download/%s"%filename).st_size
        data = pickle.dumps([filename,size,0])
        # send_size = 0
        self.sock.send(data) # send [name,size,state]

        sent_size = 0
        with self.lock: # a file can be use at the a time
            with open("Download/%s"%filename,'rb') as f:
                while sent_size < size:
                    for line in f:
                        self.sock.send(line)
                        sent_size += len(line)
                    # print("Transfer bar [%s]%%"%(sent_size/size)*100,end='\r')
            print("sending done!")

    def get(self,comm):
        import pickle
        self.sock.send(comm.encode())
        # os.chdir('./Download')  # client dir
        data = self.sock.recv(1024)
        # print("file info:", data,type(data))
        # data = data.decode()

        file_info = pickle.loads(data)  # [name,size,state]
        # print("file info:",file_info)

        total_size = file_info[1] # total size
        recv_size = 0
        filename = str(uuid.uuid1()).replace('-','')
        with self.lock:
            with open('Download/%s'%filename,'ab') as f:
                while recv_size < total_size:
                    size = total_size - recv_size
                    if size > 1024:
                        data = self.sock.recv(1024)
                    else:
                        data = self.sock.recv(size)
                    f.write(data)
                    recv_size += len(data)
                    # print("Transfer bar:[%s]%%"%(recv_size/total_size)*100,end='\r')
        if total_size == recv_size:
            print("get file done!")

    def run(self):
        while True:
            print("\033[1;34;1mfiles local:\033[0m")
            for i,f in enumerate(os.listdir("./Download"),1):
                print(i,f)
            print("\033[1;34;1mfiles server:\033[0m")
            for i, f in enumerate(os.listdir("./Upload"), 1):
                print(i, f)
            inp = input("command>>:").strip()
            # inp = 'get a'
            if inp:
                command = inp.split()
                if command[0] == 'put': # put file to server
                    if os.path.exists('Download/%s'%command[1]):
                        self.put(inp)
                    else:
                        print("local file does not exist!")

                elif command[0] == 'get':
                    if os.path.exists('./Upload/%s'%command[1]):
                        self.get(inp)
                    else:# file does not exist in server
                        print("file does not exist in server")
                else:
                    print("invalid command!")
        self.sock.close()

if __name__ == '__main__':
        client = client_ftp()
        client.run()

        # for i in range(120):
        #     client = client_ftp()
        #     t = threading.Thread(target=client.run,args=())
        #     t.start()
            # t.join()