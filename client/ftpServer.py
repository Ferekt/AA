from pyftpdlib import servers
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.authorizers import DummyAuthorizer
import threading
class ftpServer():
    def __init__(self):
        self.authorizer=DummyAuthorizer()
        self.authorizer.add_user("user","kek",".",perm="elradfmwMT")
        self.handler=FTPHandler
        self.handler.authorizer=self.authorizer
        self.address = ("0.0.0.0",21)
        self.server = servers.FTPServer(self.address, self.handler)
        self.server.max_cons_per_ip=5
        self.t1=threading.Thread(target=self.ftp_serve,daemon=True)
   
    def ftp_serve(self):
        self.server.serve_forever()
        return
    
    def start_ftp(self):
        self.t1.start()
        return True