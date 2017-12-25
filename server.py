import os,time,uuid,socket,select,queue,json


ip,port = 'localhost',1212

class server_ftp():
    '''
    ftp server class
    '''
    def __init__(self):
        self.sock = socket.socket()
        self.inputs = [self.sock]
        self.outputs = []
        self.up_queue = {} # store info for upload conn
        self.down_queue = {} # store info for download conn
        self.message = {} # store data to be transfer for each conn
        #init socket
        self.sock.bind((ip,port))
        self.sock.listen(1000)
        self.sock.setblocking(0)

    def put(self,conn):
        '''
        upload
        :param conn:
        :return:
        '''
        import uuid
        if len(self.up_queue[conn]) == 1: # not ready
            data = json.loads(conn.recv(1024).decode()) # recv [name,size,state]
            self.up_queue[conn] = data
            filename = uuid.uuid1()
            self.up_queue[conn].append(filename)  # unique filename [3]
        else:  # continue sending date
            data = conn.recv(1024)
            size = self.up_queue[conn][1]
            state = self.up_queue[conn][2]
            if size > state :  # continue recv
                with open("./Upload/%s"%self.up_queue[conn][3],'ab') as f:
                    f.write(data)
                    state += len(data)
                self.up_queue[conn][2] = state
            else:
                print("recv has finished!")
                # rename filename
                if os.path.exists("./Upload/%s"%self.up_queue[conn][0]):
                    os.remove("./Upload/%s"%self.up_queue[conn][0])
                os.rename("./Upload/%s"%self.up_queue[conn][3],"./Upload/%s"%self.up_queue[conn][0])
    def get(self,conn):
        '''
        download
        :param conn:
        :return:
        '''
        pass
    def read(self,conn):
        if conn in self.up_queue: # Uploading...
            self.put(conn)
        elif conn in self.down_queue: # Downloading...
            self.get(conn)
        else: # command or file info
            data = conn.recv(1024).decode()
            if data:
                print("Recv client request:", data)
                command = data.split()
                if command[0] == 'get':
                    self.get(conn)
                    self.up_queue[conn]=[command[1]] # {conn:[filename,size,state]}
                elif command[0] == 'put':
                    self.put(conn)
                    self.down_queue[conn] = [command[1]] # {conn:[filename,size,state]}
                # else:
                #     self.message[conn].put('Invalid command!!!')
            else:
                self.clear(conn)
    def write(self,conn):
        pass
    def clear(self,conn):
        '''
        clear conn
        :param conn:
        :return:
        '''
        if conn in self.outputs:
            self.outputs.remove(conn)
        if conn in self.up_queue:
            del self.up_queue[conn]
        if conn in self.down_queue[conn]:
            del self.down_queue[conn]
        self.inputs.remove(conn)
        del self.message[conn]
        conn.closed()
    def run(self):
        '''
        listen specified list and deal with socket
        :return:
        '''
        readable,writable,exception = select.select(self.inputs,self.outputs,self.inputs)
        for r in readable:
            if r is self.sock: # new client
                conn, addr = r.accept()
                conn.setblocking(False)
                print("A client has connected in:", addr)
                self.inputs.append(conn)
                self.message[conn] = queue.Queue()  #
            else: # old client
                self.read(r)
        for w in writable:
            self.write(w)
        for e in exception:
            self.clear(e)