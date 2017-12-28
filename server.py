import os,time,uuid,socket,select,queue,pickle

ip,port = 'localhost',8888
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
        self.put_queue = {} # store info for upload conn {conn:[name,size..]}
        self.get_queue = {} # store info for download conn {conn:[name,size..]}
        self.message = {} #  {conn:queue.Queue()}
        #init socket
        self.sock.bind((ip,port))
        self.sock.listen(1000)
        self.sock.setblocking(0)

    def put(self,conn,data):
        '''
        upload
        :param conn:
        :return:
        '''
        import uuid
        if len(self.put_queue[conn]) == 1: # not ready,wait for file info
            # data = conn.recv(1024)
            info = pickle.loads(data) # recv [name,size,state]
            self.put_queue[conn] = info
            filename = str(uuid.uuid1()).replace('-','')
            self.put_queue[conn].append(filename)  # unique filename [3]
            # print("file info:",self.put_queue[conn])
            # [real_name,size,recv_size,unique_name]

        else:  # continue sending date
            size = self.put_queue[conn][1]
            state = self.put_queue[conn][2]
            if state < size:
                with open("Upload/%s"%self.put_queue[conn][3],'ab') as f:
                    f.write(data)
                    self.put_queue[conn][2] += len(data)

            # finish receiving
            if size == self.put_queue[conn][2]:
                # rename filename
                if os.path.exists("Upload/%s"%self.put_queue[conn][0]):
                    os.remove("Upload/%s"%self.put_queue[conn][0])
                os.rename("Upload/%s"%self.put_queue[conn][3],"Upload/%s"%self.put_queue[conn][0])
                # print("recv has finished!")
                self.put_queue.pop(conn)  # clear put_queue
                # if conn in self.outputs:
                #     self.outputs.remove(conn)
    def get(self,conn,):
        '''
        download
        :param conn:
        :return:
        '''
        try:
            data = self.message[conn].get_nowait()
        except queue.Empty:
            # print("send file done!")
            self.get_queue.pop(conn)  # remove conn from get_queue
            self.outputs.remove(conn)
        else:
            # print("queue data:",data)
            conn.send(data)

    # def filter(self,conn):
    #     '''
    #     filter receiving data,lead to correct func
    #     :param conn:
    #     :return:
    #     '''
    #     data = conn.recv(1024)
    #     if data:
    #         if conn in self.put_queue: # Uploading...
    #             self.put(conn)
    #         elif conn in self.get_queue: # Downloading...
    #             self.get(conn)
    #         else: # command or file info
    #             # data = conn.recv(1024).decode()
    #             # print("Recv client request:", data)
    #             # if data:
    #             command = data.split()
    #             if command[0] == 'put': # get filename
    #                 self.put_queue[conn] = [command[1]]  # {conn:[filename,]}
    #
    #             elif command[0] == 'get': # put filename
    #                 self.get_queue[conn] = [command[1]]
    #                 size = os.stat("./Upload/%s"%command[1]).st_size
    #                 self.get_queue[conn].append(size)
    #                 self.get_queue[conn].append(500) # {conn:[name,size,state]}
    #                 self.message[conn].put(self.get_queue[conn]) # insert to queue
    #                 self.outputs.append(conn) # add to writable listen list
    #                 # load file data
    #                 with open("./Upload/%s" % command[1], 'rb') as f:
    #                     for line in f:
    #                         self.message[conn].put(line)
    #     else:
    #         print("A cliend has disconnected!", conn)
    #         # self.clear(conn)
    def write(self,conn):
        if self.get_queue[conn][2] == 500 : # code 500 -->not ready,send file info
            data = self.message[conn].get()
            send_data = pickle.dumps(data)
            conn.send(send_data)  # [name,size,state]
            self.get_queue[conn][2] = 200  # code 200 -->change state
        else:
            self.get(conn)

    def readable(self,conn,data):
        if conn in self.put_queue:  # Uploading...
            self.put(conn,data)
        elif conn in self.get_queue:  # Downloading...
            self.get(conn)
        else:
            command = data.decode().split()
            # print("recv data:",command)
            if command[0] == 'put':  # get filename
                self.put_queue[conn] = [command[1]]  # {conn:[filename,]}

            elif command[0] == 'get':  # put filename
                # self.get_queue[conn] = [command[1]]
                size = os.stat("Upload/%s" % command[1]).st_size
                self.get_queue[conn] = [command[1],size,500]
                # self.get_queue[conn].append(500)  # {conn:[name,size,state]}
                self.message[conn].put(self.get_queue[conn])  # insert to queue
                self.outputs.append(conn)  # add to writable listen list
                with open("Upload/%s" % command[1], 'rb') as f:
                    for line in f:
                        self.message[conn].put(line)

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
        self.inputs.remove(conn)
        del self.message[conn]
        conn.closed()
    def run(self):
        '''
        listen specified list and deal with socket
        :return:
        '''
        while True:
            readable,writable,exception = select.select(self.inputs,self.outputs,self.inputs)
            for r in readable:
                if r is self.sock:  # new client connected in
                    conn, addr = r.accept()
                    # conn.setblocking(False)
                    print("A client has connected in:", conn)
                    self.inputs.append(conn)
                    self.message[conn] = queue.Queue()  #
                else:  # old client sending data
                    try:
                        data = r.recv(1024)
                        if data:
                            # print("type:",type(data))
                            self.readable(r,data)
                        else:
                            print(" a client has disconnected")
                            self.inputs.remove(r)
                            if r in self.put_queue:
                                self.put_queue.pop(r)
                            if r in self.get_queue:
                                self.get_queue.pop(r)
                    except ConnectionResetError as e:
                        print("client error by e:",e)
                        self.inputs.remove(r)
                        if r in self.outputs:
                            self.outputs.remove(r)

            for w in writable:
                self.write(w)
            for e in exception:
                if e in self.outputs:
                    self.outputs.remove(e)
                self.inputs.remove(e)
                if e in self.put_queue:
                    self.put_queue.pop(e)
                if e in self.get_queue:
                    self.get_queue.pop(e)


if __name__ == '__main__':
    server = server_ftp()
    server.run()
