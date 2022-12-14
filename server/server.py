import select, socket, sys,queue
from _thread import start_new_thread
import pickle
from message import *
from clienthandler import ClientService
BUFFER_SIZE = 1024*4

class SocketServer(): 
	def __init__(self, ctrl, ip_address, port):
		self.host = ip_address
		self.port = port
		self.maxClientCount = 40
		self.ctrl = ctrl
		self.readable= []
		self.writable= []
		self.exceptional= []
		self.clienthandler = ClientService(self)
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setblocking(0)

		try:
			self.server.bind((self.host, self.port))
		except socket.error as e:
			print(str(e))
   
		self.server.listen()
		self.inputs = [self.server]
		self.outputs = []
		self.message_queues = {}
		self.connection_service = start_new_thread(self.connection_service, ())
		print('Waitiing for a Connection..')

	def getData(self,connection):
		data = pickle.loads(connection.recv(BUFFER_SIZE))
		print(data.command(), data.container())
		return data.command(), data.container()

	def connection_service(self):
		while self.inputs:
			self.readable, self.writable, self.exceptional = select.select(
				self.inputs, self.outputs, self.inputs)
			for s in self.readable:
				if s is self.server:
					connection, client_address = s.accept()
					connection.setblocking(0)
					self.inputs.append(connection)
					self.clienthandler.connections.append(connection)
					self.clienthandler.clients_ready.append(True)
					self.clienthandler.client_addresses.append(client_address)
					self.message_queues[connection] = queue.Queue()
				else:
					dcmd,dctr = self.getData(s)
					if dcmd:
						self.clienthandler.handle(dcmd,dctr,s)
					else:
						if s in self.outputs:
							self.outputs.remove(s)
						self.inputs.remove(s)
						s.close()
						del self.message_queues[s]

			for s in self.writable:
				try:
					next_msg = self.message_queues[s].get_nowait()
				except queue.Empty:
					self.outputs.remove(s)
				else:
					s.send(pickle.dumps(next_msg))

			for s in self.exceptional:
				self.inputs.remove(s)
				if s in self.outputs:
					self.outputs.remove(s)
				s.close()
				del self.message_queues[s]
		print("faszom")