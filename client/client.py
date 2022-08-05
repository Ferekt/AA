import socket
import pickle
from message import *
import importlib
import saves as s
import ftpServer
import os
import threading
from pyftpdlib import servers
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.authorizers import DummyAuthorizer


BUFFER_SIZE = 1024*4
SEPARATOR = "<SEPARATOR>"

class Client():
	def __init__(self):
		self.ClientSocket = socket.socket()
		self.host = '192.168.0.186'
		self.port = 53000
		self.Algorithm = None
		self.algorithm_name = None
		self.ftpS=ftpServer.ftpServer()
	"""
	def ftp_serve(self):
		authorizer=DummyAuthorizer()
		authorizer.add_user("user","kek",".",perm="elradfmwMT")
		handler=FTPHandler
		handler.authorizer=authorizer
		address = ("0.0.0.0",21)
		server = servers.FTPServer(address, handler)
		server.max_cons_per_ip=5
		server.serve_forever()"""
		
	def sendData(self, data):
		self.ClientSocket.send(pickle.dumps(data))

	def getData(self):
		data = pickle.loads(self.ClientSocket.recv(BUFFER_SIZE))
		return data.command(), data.container()
	
	def getFile(self):
		filename, filesize = self.getData()
		print("receieving", filename, filesize)
		
		filesize = int(filesize)
		with open(filename, "wb") as f:
			while True:
				bytes_read = self.ClientSocket.recv(BUFFER_SIZE)
				if bytes_read[-3:] == b'eof':    
					f.write(bytes_read[:-3])
					break
				f.write(bytes_read)		
		print("file written" + filename)


	def connect(self):
		print('Waiting for connection')
		try:
			self.ClientSocket.connect((self.host, self.port))
		except:
			print("there's no connection")
			return False
		print("connected")
		return True

	def run(self):
		connection = self.connect()
		while connection:

			try:
				dcmd, dctr = self.getData()
			except:
				print("connection lost")
				break
			print("got:",dcmd, dctr)
			cmd, ctr = None, None

			
			if dcmd == "exit":
				print("disconnected by server")
				break

			elif dcmd == "name":
				#s.createFolder("./algorithms/" + dctr  + "/resources/")	
				if True:
					self.algorithm_name = dctr
					cmd = "name_written"
				else:
					cmd = "name_writing_error"

			elif dcmd == "file":
				self.getFile()
				cmd, ctr = "file_written", None

			elif dcmd == "import":
				self.Algorithm = importlib.import_module("algorithms."+self.algorithm_name+".resources.algorithm").Algorithm(size=0)
				cmd, ctr = "import_done", None

			elif dcmd == "calculate":
				self.Algorithm.population = dctr	
				self.Algorithm.client_evolve()
				scores = self.Algorithm.population[0].score
				cmd, ctr = "result", scores

			elif dcmd == "wait":
				print("waiting...")
				cmd, ctr = "wait", None

			elif dcmd =="path":
				cmd,ctr= "path", os.path.dirname(os.path.abspath(__file__))
			
			elif dcmd == "Turn_on":
				if self.ftpS.start_ftp():
					cmd,ctr="Done",None

			elif dcmd == "Turn_off":
				self.ftpS.server.close_when_done()


				
			else:
				print("Invalid command receieved")
				print(dcmd)
				print(dctr)
				cmd, ctr = "print", "Command not found"
				break

			print("sent:",cmd, ctr)
			try:
				self.sendData(Message(cmd, ctr))
			except:
				print("connection lost in sending")
				break

		print("shutting down")
		self.ClientSocket.close()




if __name__ == "__main__":
	client = Client()
	client.run()


