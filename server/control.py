from hashlib import new
from http import client
import importlib
from multiprocessing.connection import wait
from operator import contains
from time import sleep
import numpy as np
import saves as s
import server
import torch


class Control():
	def __init__(self):
		self.populationTracker = None
		self.finishTracker = None
		self.task = "WAIT"
		self.client_queues =[]
		self.ready_clients=[]
		self.clients_transferring=[]
		self.done_clients=[]
		self.is_updated=False
		self.Server = server.SocketServer(self, '10.0.6.1' , 53000)
		self.Algorithm = None

		self.algorithm_name = None
		self.algorithm_resources = None

		self.algorithm_folder = None
		self.experiment_changed = False

		self.experiments_root_folder = None
		self.experiment_name = None
		self.experiment_folder = None
		self.resources_folder = None

	def reset_parameters(self):
		self.populationTracker = None
		self.finishTracker = None
		self.task = "WAIT"
		self.Algorithm = None
		self.algorithm_name = None
		self.algorithm_resources = None
		self.algorithm_folder = None
		self.experiment_changed = False
		self.experiments_root_folder = None
		self.experiment_name = None
		self.experiment_folder = None
		self.resources_folder = None

	def import_algorithm(self, name):
		self.experiment_changed = True
		self.algorithm_name = name
		self.experiment_name = None
		self.algorithm_resources = importlib.import_module("algorithms."+name+".resources.algorithm")
		self.algorithm_folder = "./algorithms/" + self.algorithm_name + "/"
		self.experiments_root_folder = self.algorithm_folder + "experiments/"
		self.resources_folder = self.algorithm_folder + "resources/"
		s.createFolder(self.experiments_root_folder)
	
	def save_experiment(self):
		return s.save(self.Algorithm, self.experiment_folder, str(self.Algorithm.epochs))

	def create_experiment(self, name):
		if self.algorithm_name:
			self.experiment_changed = True
			self.experiment_name = name
			self.experiment_folder = self.experiments_root_folder + name + "/"
			s.createFolder(self.experiment_folder)
			self.Algorithm = self.algorithm_resources.Algorithm()
			self.populationTracker = np.ones(len(self.Algorithm.population), dtype=bool)
			self.finishTracker = np.zeros(len(self.Algorithm.population), dtype=bool)
			self.save_experiment()
		else:
			print("import algorithm first!")
	
	def load_experiment(self, name, number):
		self.experiment_changed = True
		self.experiment_folder = self.experiments_root_folder + name + "/"
		self.Algorithm = s.load(self.experiment_folder, number)
		self.experiment_name = name
		self.populationTracker = np.ones(len(self.Algorithm.population), dtype=bool)
		self.finishTracker = np.zeros(len(self.Algorithm.population), dtype=bool)


	def set_task(self, task):
		for c in self.Server.clients:
			c.is_ready = False

		self.task = task
		while not all([c.is_ready for c in self.Server.clients]) or not self.Server.clients:
			pass

		self.task = "WAIT"
  
  
	def send_to_clients(self):
		self.Server.clienthandler.handle("SEND",None,Server)
		

	def evolution(self, number_of_epochs):
		self.Server.clienthandler.handle("EVOLVE",number_of_epochs,Server)
        

	def printmenu(self):
		generation = None
		if self.Algorithm:
			generation = self.Algorithm.epochs
		print('''
	Address:    {}:{}
	Clients:    {}/{}
	Algorithm:  {}
	Generation: {}
	Experiment: {}
	clients {}
		'''.format(self.Server.host,self.Server.port,len(self.Server.clienthandler.connections),self.Server.maxClientCount,self.algorithm_name,
			generation, self.experiment_name, self.Server.readable))

	def get_data(self):
		epoch = None
		if self.Algorithm:
			epoch = self.Algorithm.epochs
		return {
			"IP address"		: self.Server.host,
			"Port"				: self.Server.port,
			"Current clients"	: len(self.Server.clients),
			"Max clients"		: self.Server.maxClientCount,
			"Client list"		: [c.address for c in self.Server.clients],


			"Algorithm"			: self.algorithm_name,
			"Experiment"		: self.experiment_name,
			"Epoch"				: epoch
		}




if __name__ == "__main__":
	
	Server = Control()
	torch.autograd.set_grad_enabled(False)
	
	while True:
		Server.printmenu()
		choice = input("choose an action by typing its character in parenthesys:\n(i)mport/(e)volve/sendto(h)ost/(s)ave/(l)oad/(q)uickload/(c)reate/(d)isconnect/e(x)it  :\n")
  
		if choice == "i":
			finished = False
			if Server.algorithm_resources is not None:
				print("an algorithm is already loaded, importing may cause errors")
				ans = input("(not likely, but still) are you sure? (y/n)")
				if ans == "y" or ans == "Y": 
					pass
				else:
					finished = True

			while not finished:
				s.printDir("./algorithms/")
				name = input("algorithm name?")
				if name in s.listDir("./algorithms/"):
					Server.import_algorithm(name)
					finished = True

		elif choice == "q":
			Server.import_algorithm("GA")
			Server.load_experiment("Feri","0.gen")
		
		elif choice == "h":
			Server.send_to_clients()
			print("kint")

   
		elif choice == "e":
			good_input = False
			epoch = None
			while not good_input:
				try:
					epoch = int(input("number of epochs: "))
					if epoch < 1:
						print("give a positive integer")
					else:
						good_input = True
				except:
					print("give an integer")
			Server.evolution(epoch)
				

		elif choice == "c":
			finished = False
			while not finished:
				name = input("type a new experiment name: ")
				if name in s.listDir(Server.experiments_root_folder):
					print("an experiment already exists with that name")
					ans = input("overvrite? (y/n)")
					if ans == "y" or ans == "Y":
						s.deleteFolder(Server.experiments_root_folder + name)
						finished = True
				else:
					finished = True
			Server.create_experiment(name)		

		elif choice == "s":
			Server.save_experiment()

		elif choice == "l":
			finished = False
			while not finished:
				s.printDir(Server.experiments_root_folder)
				name = input("experiment name:")
				if name in s.listDir(Server.experiments_root_folder):
					while not finished:
						s.printDir(Server.experiments_root_folder + name)
						number = input("generation number:")
						file = str(number) + ".gen"
						if file in s.listDir(Server.experiments_root_folder + name):
							Server.load_experiment(name, file)
							finished = True


		elif choice == "d":
			Server.Server.disconnect_all()

		elif choice == "x":
			Server.Server.disconnect_all()
			break
		else:
			print("invalid command")


	print("shutting down")
	Server.Server.ServerSocket.close()
