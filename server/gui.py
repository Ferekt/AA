#!/home/stickyfur/Documents/_diploma/venv/bin/python3.8
from control import Control
from _thread import start_new_thread
import saves as s
import PySimpleGUI as sg

CONTROLLER_OBJECT = Control()
EXPERIMENT = ["Algorithm","Experiment","Epoch"]
SERVER = ["IP address", "Port", "Current clients", "Max clients"]
DATA = CONTROLLER_OBJECT.get_data()
PARAMETERS = {}

def imp():
	LIST = s.listDir("./algorithms/")

	layout = [  [sg.Text('Choose an algorithm!')],
				[sg.Listbox(LIST, size=(20,4), enable_events=True, key='_LIST_')],
				[sg.Input(do_not_clear=True, size=(20,1),enable_events=True, key='_INPUT_')],
				[sg.Text('Selected: '),sg.Text('None',key="disp")],
				[sg.Button('Cancel'), sg.Button('Import')]	]

	window = sg.Window('Import').Layout(layout)
	item = None
	while True:
		event, values = window.Read()
		if event is None or event == 'Cancel':
			break
		
		if values['_INPUT_'] != '':
			search = values['_INPUT_']
			new_values = [x for x in LIST if search in x]
			window.Element('_LIST_').Update(new_values)
		else:
			window.Element('_LIST_').Update(LIST)
		
		if event == '_LIST_' and len(values['_LIST_']):
			item = values['_LIST_'][0]
			window.FindElement("disp").Update(item)

		if event == 'Import' and item:
			CONTROLLER_OBJECT.import_algorithm(item)
			break

	window.Close()

def load():
	if CONTROLLER_OBJECT.algorithm_name:
		LIST = s.listDir(CONTROLLER_OBJECT.experiments_root_folder)
		LIST2 = []
		layout = [  [sg.Text('Choose an experiment!')],
					[sg.Listbox(LIST, size=(20,4), enable_events=True, key='_LIST_'),
					sg.Listbox(LIST2, size=(20,4), enable_events=True, key='_LIST2_')],
					[sg.Input(do_not_clear=True, size=(20,1),enable_events=True, key='_INPUT_')],
					[sg.Text('Selected:   '),sg.Text('None',size=(20,0),key="disp")],
					[sg.Text('Generation: '),sg.Text('None',size=(10,0),key="disp2")],
					[sg.Button('Cancel'), sg.Button('Load')]	]

		window = sg.Window('Load').Layout(layout)
		item = None
		item2 = None
		while True:
			event, values = window.Read()
			if event is None or event == 'Cancel':
				break
			
			if values['_INPUT_'] != '':
				search = values['_INPUT_']
				new_values = [x for x in LIST if search in x]
				window.Element('_LIST_').Update(new_values)
			else:
				window.Element('_LIST_').Update(LIST)
			
			if event == '_LIST_' and len(values['_LIST_']):
				item = values['_LIST_'][0]
				LIST2 = s.listDir(CONTROLLER_OBJECT.experiments_root_folder + item + "/")
				window.FindElement("disp").Update(item)
				window.FindElement("_LIST2_").Update(LIST2)

			if event == '_LIST2_' and len(values['_LIST2_'] and item):
				item2 = values['_LIST2_'][0]
				window.FindElement("disp2").Update(item2[:-4])

			if event == 'Load' and item and item2:
				CONTROLLER_OBJECT.load_experiment(item,item2)
				break
		window.Close()
	else:
		sg.Popup('Load failed','Import an algorithm first!')

def quickload():
	CONTROLLER_OBJECT.import_algorithm("GA")
	CONTROLLER_OBJECT.load_experiment("DEFAULT","0.gen")

def save():
	if CONTROLLER_OBJECT.experiment_name:
		if CONTROLLER_OBJECT.save_experiment():
			sg.Popup('Experiment saved')
		else:
			sg.Popup('Save failed', 'File already exists, change the experiment name or delete the file first.')
	else:
		sg.Popup('Save failed','Create or load an experiment first!')

def create():
	if CONTROLLER_OBJECT.algorithm_name:
		layout = [  [sg.Text('Choose a name!')],
					[sg.Input(do_not_clear=True, size=(20,1),enable_events=True, key='_INPUT_')],
					[sg.Button('Cancel'), sg.Button('Create')]	]

		window = sg.Window('Create').Layout(layout)
		
		while True:
			event, values = window.Read()
			if event is None or event == 'Cancel':
				break

			if event == 'Create':
				if values['_INPUT_']:
					if values['_INPUT_'] in s.listDir(CONTROLLER_OBJECT.experiments_root_folder):
						sg.Popup('Creation failed', 'Experiment already exists')
					else:
						CONTROLLER_OBJECT.create_experiment(values['_INPUT_'])
						break
		window.Close()
	else:
		sg.Popup('Load failed','Import an algorithm first!')

def evolve(generation_string):
	try:
		if int(generation_string) > 0:
			CONTROLLER_OBJECT.evolution(int(generation_string))
		else:
			sg.Popup('Error','\"{}\"" is not a positive natural number'.format(generation_string))
	except:
		sg.Popup('Error','\"{}\"" is not a positive natural number'.format(generation_string))

def make_main_window():
	menu_def = [
				[	'&Agent', [
						'&Import', 
					], 
				],
				[	'&Experiment', [
						'&Create',
						'&Save',
						'&Load',
						'&Show parameters'
					],
				],
				[	'&Server', [
						'&Reinit'
					],
				],

				#['&Help', '&About...'],
	]
	

	main_layout = [
		[sg.Menu(menu_def, tearoff=True)],
		
		[sg.Text('Information', size=(30, 1), justification='center', relief=sg.RELIEF_RIDGE)
		],
		[sg.Frame('',[
			[sg.Frame('Server',[
				[sg.Text(key, size=(15, 0)),
				sg.Text(DATA[key], size=(10, 0), key=key),
				] for key in DATA if key in SERVER
				]),
			],
			[sg.Frame('Agent',[
				[sg.Text(key, size=(15, 0)),
				sg.Text(DATA[key], size=(10, 0), key=key),
				] for key in DATA if key in EXPERIMENT
				]),
			],]),

		sg.Frame('',[
			[sg.Listbox(values=DATA["Client list"], size=(30, 12),key="Client list")
				],
			[sg.Button('Refresh'), sg.Button('Disconnect all'),],
		]),
		],
		
		[sg.Button('Experiment panel'), sg.Button('Quickload')]
		
	]

	return sg.Window('Algorithm controller', main_layout, default_element_size=(40, 1), finalize=True)

def make_experiment_window():
	if CONTROLLER_OBJECT.experiment_name:
		PARAMETERS = CONTROLLER_OBJECT.Algorithm.get()
		layout = [[sg.Frame('Parameters',[
					[sg.Text(key, size=(20, 0)),
					sg.Text(PARAMETERS[key], size=(15, 0),key=key+"old"),
					sg.InputText(PARAMETERS[key], size=(15, 0),key=key),
					] for key in PARAMETERS
					]),sg.Button('Set')],
				[sg.Button('Cancel'),  sg.Button('Evolve'),sg.InputText("#", size=(4, 0),key="generation_count")],
				]

		return sg.Window('Experiment panel', layout, finalize=True)
	else:
		sg.Popup('Error','Load or create experiment first!')


if __name__ == "__main__":
	window_main = make_main_window()
	window_experiment = None


	while True:

		window, event, values = sg.read_all_windows()


		if event in ("Cancel", sg.WIN_CLOSED):
			if window == window_main:
				if window_experiment:
					window_experiment.close()
				window_main.close()
				break
			window.close()
			window = None


		if window == window_main:
			if event == "Refresh":
				pass
			if event == "Import":
				imp()
			if event == "Create":
				create()
			if event == "Save":
				save()
			if event == "Load":
				load()
			if event == "Quickload":
				quickload()
			if event == "Disconnect all":
				CONTROLLER_OBJECT.Server.disconnect_all()

		if event == "Experiment panel":
			if window_experiment:
				window_experiment.close()
				window_experiment = None
			window_experiment = make_experiment_window()

		if window_experiment:
			if window == window_experiment:
				if event == "Set":
					PARAMETERS = values
					if not CONTROLLER_OBJECT.Algorithm.set(PARAMETERS):
						sg.Popup('Error','Incorrect data!')
					PARAMETERS = CONTROLLER_OBJECT.Algorithm.get()
					for key in PARAMETERS:
						window_experiment.FindElement(key+"old").Update(PARAMETERS[key])
				if event == "Evolve":
					evolve(values["generation_count"])

		
		DATA = CONTROLLER_OBJECT.get_data()
		for key in EXPERIMENT + SERVER + ["Client list"]:
			window_main.FindElement(key).Update(DATA[key]) 

		

	if CONTROLLER_OBJECT.Server.clients:
		CONTROLLER_OBJECT.Server.disconnect_all()
	
	print("shutting down")
	CONTROLLER_OBJECT.Server.ServerSocket.close()






'''

names = ['Roberta', 'Kylie', 'Jenny', 'Helen',
		'Andrea', 'Meredith','Deborah','Pauline',
		'Belinda', 'Wendy']

layout = [  [sg.Text('Listbox with search')],
			[sg.Input(do_not_clear=True, size=(20,1),enable_events=True, key='_INPUT_')],
			[sg.Listbox(names, size=(20,4), enable_events=True, key='_LIST_')],
			[sg.Button('Chrome'), sg.Button('Exit')]]

window = sg.Window('Listbox with Search').Layout(layout)
# Event Loop
while True:
	event, values = window.Read()
	if event is None or event == 'Exit':                # always check for closed window
		break
	if values['_INPUT_'] != '':                         # if a keystroke entered in search field
		search = values['_INPUT_']
		new_values = [x for x in names if search in x]  # do the filtering
		window.Element('_LIST_').Update(new_values)     # display in the listbox
	else:
		window.Element('_LIST_').Update(names)          # display original unfiltered list
	if event == '_LIST_' and len(values['_LIST_']):     # if a list item is chosen
		sg.Popup('Selected ', values['_LIST_'])

window.Close()

'''


#Server = server.SocketServer()
'''
algorithms = s.listDir("./algorithms/")
experiments = []
generations = []

layout = [

	[sg.Listbox(list(algorithms),
				enable_events=True,
				select_mode='extended',
				size=(None, 10),
				auto_size_text=True,
				key='Algorithm'),

	 sg.Listbox(list(experiments),
				enable_events=True,
				select_mode='extended',
				size=(None, 10),
				auto_size_text=True,
				key='Experiment'),

	 sg.Listbox(list(generations),
				enable_events=True,
				select_mode='extended',
				size=(None, 10),
				auto_size_text=True,
				key='Generation'),
	],
]



window = sg.Window('Load', layout,
	keep_on_top=True,
	resizable=True,
	)

while True:
	event, values = window.Read()
	
	if values['Algorithm']:
		experiments = s.listDir("./algorithms/" + values['Algorithm'][0] + "/experiments/")
	
	if values['Experiment']:
		generations = s.listDir("./algorithms/" + values['Algorithm'][0] + "/experiments/" + values['Experiment'][0] + "/")


	window.Element('Experiment').Update(experiments)
	window.Element('Generation').Update(generations)

	if not event:
		break
	if event in ('Algorithm', 'Experiment', 'Generation'):
		print(values)


'''