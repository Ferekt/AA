import socket
from _thread import start_new_thread
import clienthandler


class SocketServer(): 
	def __init__(self, ctrl, ip_address, port):
		self.ServerSocket = socket.socket()
		self.host = ip_address
		self.port = port
		self.maxClientCount = 3
		self.ctrl = ctrl


		try:
			self.ServerSocket.bind((self.host, self.port))
		except socket.error as e:
			print(str(e))
		print('Waitiing for a Connection..')
		
		self.clients = []
		self.connection_service = start_new_thread(self.connection_service, ())
		self.ServerSocket.listen(100)

	
	def connect(self):
		Client, address = self.ServerSocket.accept()
		print('Connected to: ' + address[0] + ':' + str(address[1]))
		new_client = clienthandler.ClientService(Client, address, self.ctrl)
		new_client.start()
		self.clients.append(new_client)
		print('Thread Number: ' + str(len(self.clients)))

	def connection_service(self):
		ismaximal = True
		while True:	
			if len(self.clients) < self.maxClientCount:
				if ismaximal:
					ismaximal = False
					print("connecting clients")
				self.connect()
			else:
				if not ismaximal:
					ismaximal = True
					print("maximum reached")


	def disconnect_all(self):
			for c in self.clients:
				c.disconnect()
			while self.clients:
				pass
	
	