import os,time,uuid,socket,select,queue,json


ip,port = 'localhost',1212
# a = queue.Queue()
# a.empty()
class server_ftp():
    '''
    ftp server class
    '''
    def __init__(self):
        self.sock = socket.socket()
        self.inputs = [self.sock]
        self.outputs = []
        self.put_queue = {} # store info for upload conn
        self.get_queue = {} # store info for download conn
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
        if len(self.put_queue[conn]) == 1: # not ready,wait for file info
            data = json.loads(conn.recv(1024).decode()) # recv [name,size,state]
            self.put_queue[conn] = data
            filename = str(uuid.uuid1()).replace('-','')
            self.put_queue[conn].append(filename)  # unique filename [3]
            # [real_name,size,recv_size,unique_name]

        else:  # continue sending date
            size = self.put_queue[conn][1]
            state = self.put_queue[conn][2]
            if size > state :  # continue recv
                remain = size - state
                if remain > 1024:
                    data = self.sock.recv(1024)
                else:
                    data = self.sock.recv(remain)
                with open("./Upload/%s"%self.put_queue[conn][3],'ab') as f:
                    f.write(data)
                    self.put_queue[conn][2] += len(data)

            # finish receiving
            if size == self.put_queue[conn][2]:
                print("recv has finished!")
                self.put_queue.pop(conn) # clear put_queue
                # rename filename
                if os.path.exists("./Upload/%s"%self.put_queue[conn][0]):
                    os.remove("./Upload/%s"%self.put_queue[conn][0])
                os.rename("./Upload/%s"%self.put_queue[conn][3],"./Upload/%s"%self.put_queue[conn][0])
    def get(self,conn):
        '''
        download
        :param conn:
        :return:
        '''
        if self.message[conn].empty(): # should send data
            filename,size, state = self.get_queue[conn][0],self.get_queue[conn][1],self.get_queue[conn][2]
            with open("./Upload/%s"%filename,'rb') as f:
                f.seek(state)
                data = f.readline()
                self.sock.send(data)
                self.get_queue[conn][2] += len(data)
            if self.get_queue[conn][1] == self.get_queue[conn][2]:
                print("file sending done!")
                self.get_queue.pop(conn) # remove conn from get_queue
                self.outputs.remove(conn)
        else: # should send file info
            data = self.message[conn].get()
            self.sock.send(json.dumps(data).encode()) # [name,size,state]

    def filter(self,conn):
        '''
        filter receiving data,lead to correct func
        :param conn:
        :return:
        '''
        if conn in self.put_queue: # Uploading...
            self.put(conn)
        elif conn in self.get_queue: # Downloading...
            self.get(conn)
        else: # command or file info
            data = conn.recv(1024).decode()
            print("Recv client request:", data)
            command = data.split()
            if command[0] == 'put': # get filename
                self.put_queue[conn] = [command[1]]  # {conn:[filename,]}

            elif command[0] == 'get': # put filename
                self.get_queue[conn] = [command[1]]
                size = os.stat("./Upload/%s"%command[1]).st_size
                self.get_queue[conn].append(size)
                self.get_queue[conn].append(0) # {conn:[name,size,state]}
                self.message[conn].put(self.get_queue[conn]) # insert to queue
                self.outputs.append(conn) # add to writable listen list
            # else:
            #     self.message[conn].put('Invalid command!!!')
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
        if conn in self.put_queue:
            del self.put_queue[conn]
        if conn in self.get_queue[conn]:
            del self.get_queue[conn]
        self.inputs.remove(conn)
        del self.message[conn]
        # conn.closed()
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
                print("A client has connected in:", conn)
                self.inputs.append(conn)
                self.message[conn] = queue.Queue()  #
            else: # old client
                self.filter(r)
        for w in writable:
            self.get(w)
        for e in exception:
            self.clear(e)
if __name__ == '__main__':
    server = server_ftp()
    server.run()