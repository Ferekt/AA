from hashlib import new
import socket
import pickle
from message import *
import importlib
import saves as s
import ftpServer
import os
import client_transferhandler


BUFFER_SIZE = 1024*4
SEPARATOR = "<SEPARATOR>"

class Client():
	def __init__(self):
		self.ClientSocket = socket.socket()
		self.host = '192.168.0.144'
		self.port = 53000
		self.Algorithm = None
		self.algorithm_name = None
		self.ftpS=ftpServer.ftpServer()
		self.ftpS.start_ftp()
		self.clienttransferhandler=client_transferhandler.ClientTransferHandler(self)

	def sendData(self, data):
		self.ClientSocket.send(pickle.dumps(data))

	def getData(self):
		data = pickle.loads(self.ClientSocket.recv(BUFFER_SIZE))
		return data.command(), data.container()

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

			elif dcmd == "transfer":
				self.clienttransferhandler.transfer(dctr)
				cmd,ctr = "transfer done", dctr
			else:
				print("Invalid command receieved")
				print(dcmd)
				print(dctr)
				cmd, ctr = "print", "Command not found"
				break
			

			try:
				self.sendData(Message(cmd, ctr))
			except:
				print("connection lost in sending")
				break
		
		self.ftpS.thread_run = False
		print("shutting down")
		self.ClientSocket.close()




if __name__ == "__main__":
	client = Client()
	client.run()


