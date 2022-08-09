import numpy as np
import gym
from algorithms.GA.resources.net import *
import torch.nn
from algorithms.GA.resources.enviroments.InvPendulumTut.gymPendulum import PendulumEnv

from gym import spaces
from gym.utils import seeding
from matplotlib import pylab as plt


'''
class Algorithm():
	self.epochs			--> integer
	self.population
		-> population[0].score

	functions:
	self.client_evolve	--> should set score to population members, do parallel work
	self.server_evolve  --> do what you can't do parallel

	self.get 			--> returns a dictionary { "something" : self.data }
	self.set  			--> gets a dictionary and sets changes self.data = DICT["something"]

	self.simulate ?
'''

torch.autograd.set_grad_enabled(False)

class Algorithm():
	def __init__(self, size = 50,               		#number of agents in each generation
						mutation_rate = 0.1,    		#probability of changing a gene
						bias_mutation_rate = 0.01,		#probability of changing bias
						selection_rate = 0.5,   		#rate of the living to keep
						not_to_mutate = 0.2,    		#rate of the not mutated    (<selection rate)
						can_breed = 0.2,        		#rate of who can breed      (<selection rate)
						nn_structure = [],				#neuron counts in each layer [in, hidden1, hidden2 ..., out]
						simulation_timesteps = 10000,	#timesteps of the gym environment in each epoch
						gym_env = "Pendulum-v1"			#name of the gym environment
						):
		
		self.env_name = gym_env
		self.env = gym.make(gym_env)
		print(self.env)
			#MountainCar-v0
			#CartPole-v1
			#MountainCarContinuous-v0
			#Acrobot-v1
			#Pendulum-v0

		actionsample = self.env.action_space.sample()
		self.nnOutType = type(actionsample)


		if nn_structure == []:
			nn_structure.append(len(self.env.observation_space.sample()))
			if self.nnOutType == type(int()):
				nn_structure.append(1)
			elif self.nnOutType == type(np.ndarray([])):
				nn_structure.append(len(actionsample))
				
		self.epochs = 0	
		self.size = size
		self.mr = mutation_rate
		self.bmr = bias_mutation_rate
		self.sr = selection_rate
		self.nm = not_to_mutate
		self.cb = can_breed
		self.st = simulation_timesteps

		self.nnStructure = nn_structure

		self.population = [Net(self.nnStructure) for _ in range(self.size)]
		print(self.nnStructure)
		if self.population:
			self.best = self.population[0]

	def get(self):
		return {
			"size" 					: self.size,
			"mutation_rate" 		: self.mr,
			"bias_mutation_rate" 	: self.bmr,
			"selection_rate" 		: self.sr,
			"not_to_mutate" 		: self.nm,
			"can_breed" 			: self.cb,
			"simulation_timesteps" 	: self.st,
		}



	def set(self, DICT):
		DICT["size"] 					= int(DICT["size"])
		DICT["mutation_rate"] 			= float(DICT["mutation_rate"])
		DICT["bias_mutation_rate"] 		= float(DICT["bias_mutation_rate"])
		DICT["selection_rate"] 			= float(DICT["selection_rate"])
		DICT["not_to_mutate"] 			= float(DICT["not_to_mutate"])
		DICT["can_breed"] 				= float(DICT["can_breed"])
		DICT["simulation_timesteps"] 	= int(DICT["simulation_timesteps"])

		self.size 	= DICT["size"]
		self.mr 	= DICT["mutation_rate"]
		self.bmr 	= DICT["bias_mutation_rate"]
		self.sr 	= DICT["selection_rate"]
		self.nm 	= DICT["not_to_mutate"]
		self.cb 	= DICT["can_breed"]
		self.st 	= DICT["simulation_timesteps"]

		#processing if necessary

		return True
	
	def decide_action(self, individual, observation):
		if self.nnOutType == type(int()):
			return round(individual.forward(torch.tensor(observation).float())[0])
		elif self.nnOutType == type(float()):
			return individual.forward(torch.tensor(observation).float())[0]
		elif self.nnOutType == type(np.ndarray([])):
			return individual.forward(torch.tensor(observation).float())

	def selection(self):
		self.population = sorted(self.population,
			key=lambda i: i.score, reverse=True)[:int(self.sr*self.size)]
		
		self.best = self.population[0]


	def mutation(self):
		for individual in self.population[int(self.size*self.nm):]:
			for layer in individual.model:
				if type(layer) == nn.Linear:
					x = layer.weight.numpy()
					mask = np.random.choice([0, 1], size=x.shape,
											p=((1 - self.mr), self.mr)).astype(bool)
					x[mask] = np.random.rand(*x[mask].shape)-0.5
					layer.weight = torch.nn.Parameter(torch.from_numpy(x))
					if np.random.choice([0, 1],
										p=((1 - self.bmr), self.bmr)).astype(bool):
						layer.bias.data.fill_(np.random.rand()-0.5)

	def crossover(self):
		while len(self.population)<self.size:
			parents = np.random.choice(self.population[:int(self.size*self.cb)], 2)
			children = [Net(self.nnStructure), Net(self.nnStructure)]
			for tp0,tp1,tc0,tc1 in zip(parents[0].model, parents[1].model,
									children[0].model, children[1].model):
				if type(tp1) == nn.Linear:
					p0, p1 = tp0.weight.numpy(), tp1.weight.numpy()
					c0, c1 = tc0.weight.numpy(), tc1.weight.numpy()

					mask = np.random.choice([0, 1], size=p0.shape).astype(bool)

					c0[mask] = np.copy(p0[mask])
					c1[mask] = np.copy(p1[mask])
					c0[~mask] = np.copy(p1[~mask])
					c1[~mask] = np.copy(p0[~mask])

					tc0.weight = torch.nn.Parameter(torch.from_numpy(c0))
					tc1.weight = torch.nn.Parameter(torch.from_numpy(c1))

					if np.random.choice([0,1]).astype(bool):
						tc0.bias = tp0.bias
						tc1.bias = tp1.bias
					else:
						tc0.bias = tp1.bias
						tc1.bias = tp0.bias

			self.population.extend(children)

	def evaluation(self):
		for individual in self.population:
			individual.score = 0
			observation = self.env.reset()
			for _ in range(self.st):
				action = self.decide_action(individual, observation)
				observation, reward, done, _ = self.env.step(action)
				individual.score += reward
				if done:
					break
		self.env.close()

	def simulate(self):
		observation = self.env.reset()
		for _ in range(self.st):
			self.env.render()
			action = self.decide_action(self.best, observation)
			observation, _, done, _ = self.env.step(action)
			if done:
				break
		self.env.close()

	def evolve(self, epoch):
		for i in range(epoch):
			print("Evolution step: {}.".format(i+1))
			self.evaluation()
			self.selection()
			self.crossover()
			self.mutation()

	def client_evolve(self):
		self.evaluation()

	def server_evolve(self):
		self.selection()
		self.crossover()
		self.mutation()




if __name__ == "__main__":
	GA = Algorithm()
	GA.evolve(10)
	input("sim?")
	GA.simulate()
