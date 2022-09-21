from re import I
import threading
import os
import pickle
from algorithms.GA.resources.algorithm import Algorithm
from message import *
import saves as s


BUFFER_SIZE = 1024*4
lock = threading.Lock()


class ClientService(threading.Thread):
	def __init__(self, connection, address, ctrl):
		threading.Thread.__init__(self, target=self.run)
		self.connection = connection
		self.address = address
		self.algorithm_updated = False
		self.ctrl = ctrl
		self.daemon = True
		self.is_ready = False
		self.is_connected = True
		self.id=None

	def print_add(self, *args):
		print(self.address[1],*args)
	
	def getPath(self):
		self.sendData(Message("path",None))
		return(self.getData())


	def sendData(self, data):
		with lock:
			try:
				self.connection.sendall(pickle.dumps(data))
			except:
				self.print_add("sending failed", filename)
				self.is_connected = False

	def getData(self):
		data = pickle.loads(self.connection.recv(BUFFER_SIZE))
		return data.command(), data.container()


	def sendFile(self, filename):
		try:
			self.sendData(Message("file", None))
			filesize = os.path.getsize(filename)
			print(filename, filesize)

			self.sendData(Message(filename,filesize))

			with open(filename, "rb") as f:
				while True:
					bytes_read = f.read(BUFFER_SIZE)
					if not bytes_read:
						with lock:
							self.connection.sendall('eof'.encode())
						break
					with lock:
						self.connection.sendall(bytes_read)
			dcmd, _ = self.getData()
			self.print_add(dcmd + filename)
		except:
			self.print_add("sending failed", filename)
			self.is_connected = False


	def send_algorithm(self):
		cmd, ctr = "name", self.ctrl.algorithm_name
		try:
			self.sendData(Message(cmd,ctr))
			dcmd, dctr = self.getData()
		except:
			self.print_add("client lost")
			self.is_connected = False
			return

		if dcmd == "name_written":
			self.print_add("name written")
		elif dcmd == "name_writing_error":
			self.print_add("could not write name")
			self.is_connected = False
			return

		for file in s.listDir(self.ctrl.resources_folder):
			if file[-3:] == ".py":
				self.sendFile(self.ctrl.resources_folder + file)

		self.sendData(Message("import",None))
		dcmd, _ = self.getData()
		self.is_ready = True

	def disconnect(self):
		try:
			self.sendData(Message("exit"))
		except:
			self.print_add("client lost after finish")
		self.is_connected = False

	def evolution_step(self):
		self.is_ready = True
		dcmd = None
		dctr = None
		cmd = None
		ctr = None
		individual = None
		idx = None

		while not all(self.ctrl.finishTracker):
			if not individual:
				if len(self.ctrl.client_queues[self.id])>0:
						individual = self.ctrl.Algorithm.population[self.ctrl.client_queues[self.id][0]]
				if individual:
					idx = self.ctrl.client_queues[self.id][0]
					individual.score = 0
					cmd = "calculate"
					ctr = [individual]

			if not individual:
				cmd = "wait"
				
			try:
				self.sendData(Message(cmd,ctr))
			except:
				print("couldnt send")
				self.is_connected = False
				break
			

			try:
				dcmd, dctr = self.getData()
			except:
				print("couldnt get")
				self.is_connected = False
				break

			if dcmd == "result":
				print(str(idx)+" Score: " + str(dctr))
				individual.score = dctr
				self.ctrl.finishTracker[idx] = True 
				individual = None
				cmd = None
				ctr = None
				self.ctrl.client_queues[self.id].pop(0)

			elif dcmd == "wait":
				self.print_add("Waitiing...")
				break

			elif dcmd == "import_done":
				self.print_add("import done")
       
			else:
				print(dcmd)
				self.print_add("Invalid command receieved")
				response = Message("print", "Command not found")
    
		if idx != None:
			if not self.ctrl.finishTracker[idx] and not self.ctrl.populationTracker[idx]:
				self.ctrl.populationTracker[idx] = True
				self.print_add("did not finish, rolling back...")



	def run(self):
		while self.is_connected:

			if not self.is_ready:	
				if self.ctrl.task == "EVOLVE":
					self.sendData(Message("name",self.ctrl.algorithm_name))
					self.sendData(Message("import",None))
					dcmd, _ = self.getData()	
					self.evolution_step()


				elif self.ctrl.task == "SEND":
					if self.ctrl.experiment_changed:
						self.algorithm_updated = False
					self.is_ready = True
				elif self.ctrl.task == "STOP":
					self.is_ready = True

		self.connection.close()
		self.ctrl.Server.clients.remove(self)
		self.print_add("client is off")