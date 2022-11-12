from multiprocessing.connection import wait
from operator import contains
from re import I
import threading
import os
import pickle
from algorithms.GA.resources.algorithm import Algorithm
from message import *
import saves as s
import transferhandler
import numpy as np

BUFFER_SIZE = 1024*4
lock = threading.Lock()


class ClientService():
	def __init__(self,server):
		self.populationTracker = None
		self.finishTracker = None
		self.algorithm_updated = False
		self.server = server
		self.daemon = True
		self.is_ready = False
		self.is_connected = True
		self.id=None
		self.transfer_target = None
		self.sending=False
		self.break_sending=False
		self.transferhandler=transferhandler.TransferHandler(self.server.ctrl)
		self.connections=[]
		self.clients_ready=[]
		self.client_addresses=[]
		self.client_got_files=[]
		self.epochs=0
		self.client_queues=[]
		self.ready=True
		self.transfer_in=False
		self.disconnected_clients=[]

	def print_add(self, *args):
		print(self.id,*args)
	
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
			if not individual and self.ctrl.is_updated:
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
				print(str(self.id)+" "+str(idx)+" Score: " + str(dctr)+"\n")
				individual.score = dctr
				self.ctrl.finishTracker[idx] = True 
				individual = None
				cmd = None
				ctr = None
				self.ctrl.client_queues[self.id].pop(0)

			elif dcmd == "wait":
				#self.print_add("Waiting...\n")
				pass
			elif dcmd == "import_done":
				self.print_add("import done\n")
				self.algorithm_updated=True
       
			else:
				print(dcmd)
				self.print_add("Invalid command receieved")
				response = Message("print", "Command not found")
    
		if idx != None:
			if not self.ctrl.finishTracker[idx] and not self.ctrl.populationTracker[idx]:
				self.print_add("did not finish, rolling back...")
		
		
     
	"""def transfer(self,client):
		self.sendData(Message("transfer",str(client.address[0])))
		is_done=False
		while True:	
			print("yeet")
			try:
				dcmd,dctr=self.getData()
			except:
				print("couldnt get")
				self.is_connected = False
				break
			if dcmd=="transfer done":
				print("trasfer_done")
				is_done=True
				self.ctrl.ready_clients[self.id]=True
				self.ctrl.ready_clients[client.id]=True
				self.ctrl.clients_transferring[client.id]=False
				self.ctrl.done_clients[client.id]=True
				break"""	


	def handle(self,dcmd,dctr,connection):
		
		if dcmd=="SEND":
      
			for s in self.connections:
				s.send(pickle.dumps(Message("name",self.server.ctrl.algorithm_name)))
				self.clients_ready[self.connections.index(s)]=False
    
			while contains(self.clients_ready,False):
				waiting=True
    
			self.client_got_files=[]
   
			for s in self.connections:
				self.client_got_files.append(False)
    

			while contains(self.client_got_files,False):
				if not contains(self.client_got_files,True):
					self.clients_ready[0]=False
					self.transferhandler.transfer(str(self.client_addresses[0][0]))
					self.client_got_files[0]=True
					self.clients_ready[0]=True
				transfer_from=[]
				transfer_to=[]
				if not contains(self.clients_ready,False):
					for c in self.connections:
						if self.client_got_files[self.connections.index(c)]:
							transfer_from.append(c)
						else:
							transfer_to.append(c)
					print(len(transfer_from),len(transfer_to))
					for a,b in zip(transfer_from,transfer_to):
						self.clients_ready[self.connections.index(a)]=False
						self.clients_ready[self.connections.index(b)]=False
						print(self.client_addresses[self.connections.index(a)][0])
						print(self.client_addresses[self.connections.index(b)][0])
						a.send(pickle.dumps(Message("transfer",str(self.client_addresses[self.connections.index(b)][0]))))
					if len(self.disconnected_clients)>0:
						for d_client in self.disconnected_clients:
							self.client_got_files.pop(self.connections.index(d_client))
							self.client_addresses.pop(self.connections.index(d_client))
							self.clients_ready.pop(self.connections.index(d_client))
						self.disconnected_clients=[]

		
    
		elif dcmd=="name_written":
			self.clients_ready[self.connections.index(connection)]=True
			print("name_written:\n",connection)
   
		elif dcmd == "transfer done":
			print(self.client_addresses) 
			print([i for i,x in enumerate(self.client_addresses) if x[0]==dctr])
			self.client_got_files[[i for i,x in enumerate(self.client_addresses) if x[0]==dctr][0]]=True
			self.clients_ready[self.connections.index(connection)]=True
			self.clients_ready[[i for i,x in enumerate(self.client_addresses) if x[0]==dctr][0]]=True

		elif dcmd=="result":
			self.server.ctrl.Algorithm.population[self.client_queues[self.connections.index(connection)][0]].score=dctr
			self.finishTracker[self.client_queues[self.connections.index(connection)][0]]=True
			print(str(self.client_addresses[self.connections.index(connection)][0])+" "+str(self.client_queues[self.connections.index(connection)][0])+" Score: " + str(dctr)+"\n")
			self.client_queues[self.connections.index(connection)].pop(0)
			if len(self.client_queues[self.connections.index(connection)]) > 0:
				connection.send(pickle.dumps(Message("calculate",[self.server.ctrl.Algorithm.population[self.client_queues[self.connections.index(connection)][0]]])))
		
		elif dcmd=="import_done":
			self.clients_ready[self.connections.index(connection)]=True
			print("import_done")
   
		elif dcmd=="EVOLVE":
			number_of_epochs = dctr	
   
			for i in range(number_of_epochs):
				print("Epoch: "+str(i+1))
				print("pop length: "+str(len(self.server.ctrl.Algorithm.population)))
				self.server.ctrl.Algorithm.server_evolve()
				self.populationTracker = np.ones(len(self.server.ctrl.Algorithm.population), dtype=bool)
				self.finishTracker = np.zeros(len(self.server.ctrl.Algorithm.population), dtype=bool)
				print("pop length: "+str(len(self.server.ctrl.Algorithm.population)))
				print("poptracker length: "+str(len(self.populationTracker)))
				print("finishtracker lenght: "+str(len(self.finishTracker)))
				self.server.ctrl.Algorithm.epochs +=1
				
				self.client_queues=[]
				self.clients_ready=[]
				for i in range(len(self.connections)):
						self.connections[i].send(pickle.dumps(Message("name",self.server.ctrl.algorithm_name)))
						self.clients_ready.append(False)
						client_queue = []
						self.client_queues.append(client_queue)
				rounds=0 
    
				while contains(self.clients_ready,False):
					waiting = True
				self.clients_ready=[]
    
				for i in range(len(self.connections)):
					self.clients_ready.append(False)
					self.connections[i].send(pickle.dumps(Message("import",None)))
     
				while contains(self.clients_ready,False):
					waiting = True
     
				while contains(self.populationTracker, True) and rounds < 5:
					for i in range(len(self.client_queues)):
						for j in range(len(self.populationTracker)):
							if self.populationTracker[j] :
								self.client_queues[i].append(j)
								self.populationTracker[j]=False
								self.server.ctrl.Algorithm.population[j].score=0
								break
					rounds+=1
     
				for c in self.connections:
					c.send(pickle.dumps(Message("calculate",[self.server.ctrl.Algorithm.population[self.client_queues[self.connections.index(c)][0]]])))
     
				while contains(self.populationTracker, True):
						for i in range(len(self.client_queues)):
							if len(self.client_queues[i])<5:
								for j in range(len(self.populationTracker)):
									if self.populationTracker[j] :
										self.populationTracker[j]=False
										self.client_queues[i].append(j)
										self.server.ctrl.Algorithm.population[j].score=0
										break
				"""while contains (self.finishTracker, False) :
				for c in self.client_queues:
					if len(c) == 0:
						for c2 in self.client_queues: 
							if not contains([k.id==self.client_queues.index(c2) for k in self.Server.clients],True ):
								try: 
									c.append(c2[len(c2)-1])
									c2.pop(len(c2)-1)
								except:
									print("stackwarning ",c2)
									self.finishTracker"""
         
				while contains (self.finishTracker, False) :
					waiting=True
				print(self.finishTracker)
			print("cleared")
      
	"""def run(self):
		pass
		while self.is_connected:

			if not self.is_ready:	
				if self.ctrl.task == "EVOLVE":
					self.sendData(Message("name",self.ctrl.algorithm_name))
					self.sendData(Message("import",None))
					dcmd, _ = self.getData()	
					self.evolution_step()


				elif self.ctrl.task == "SEND":	
					self.sendData(Message("name",self.ctrl.algorithm_name))
					self.is_ready = True
					while True:
						if self.can_transfer:
							if not self.transfer_target==None:
								self.transfer(self.transfer_target)
								self.transfer_target=None
						if self.break_sending:
							self.break_sending=False
							print("break")
							break



     
				elif self.ctrl.task == "STOP":
					self.is_ready = True
		self.connection.close()
		self.ctrl.Server.clients.remove(self)
		self.print_add("client is off")"""