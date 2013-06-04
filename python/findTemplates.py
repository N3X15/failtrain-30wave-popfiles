import os,sys,logging as log
from keyvalues import KeyValues

templates = {}
stats={
	'warnings':0,
	'errors':0
}
def importTemplates(file):
	kv = KeyValues()
	log.info("Loading {0}".format(file))
	kv.load(file)
	for id in kv['Templates']:
		templates[id]=kv['Templates'][id]

def exportTemplates(file):
	kv = KeyValues('WaveSchedule')
	log.info("Saving to {0}...".format(file))
	kv['Templates']=KeyValues('Templates')
	for id in templates:
		kv['Templates'][id]=templates[id]
	kv.save(file)
	log.info("Saved {0} templates to {1}.".format(len(templates),file))
	
def exportPopfile(kv,file):
	log.info("Saving to {0}...".format(file))
	if 'Templates' not in kv:
		kv['Templates']=KeyValues('Templates')
	for id in templates:
		kv['Templates'][id]=templates[id]
	kv.save(file)
	log.info("Saved {0} templates to {1}.".format(len(templates),file))

def scanForInvalidTemplates(kv,file,path):
	if type(kv) is list:
		for i in range(len(kv)):
			value = kv[i]
			cwdp=path[:]
			cwdp[-1]=path[-1]+'[{0}]'.format(i)
			cwd = '/'.join(cwdp)
			#print(cwd)
			print((' '*(len(cwdp)+1))+' [{0}] = {1}'.format(i,type(value)))
			if type(value) is list or type(value) is KeyValues:
				scanForInvalidTemplates(value,file,cwdp)
				continue
		return
	for key in kv:
		value=kv[key]
		cwdp = path+[key]
		print((' '*len(cwdp))+' {0} = {1}'.format(key,type(value)))
		cwd = '/'.join(cwdp)
		if type(value) is list or type(value) is KeyValues:
			scanForInvalidTemplates(value,file,cwdp)
			continue
		if key == 'Template':
			if value not in templates:
				log.warning('{0} > {1}:  Unable to find Template "{2}"!'.format(file,cwd,key))
				stats['warnings']+=1
			if cwdp[-2].split('[')[0] != 'TFBot':
				log.warning('{0} > {1}:  Template directive contained in "{2}" instead of TFBot!'.format(file,cwd,cwdp[-2].split('[')[0]))
				stats['warnings']+=1

log.basicConfig(format='%(asctime)s [%(levelname)-8s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='warnings.log',filemode='w',level=log.DEBUG)

importTemplates('includes/robot_standard.pop')
importTemplates('includes/robot_giant.pop')

log.info('Loaded {0} templates.'.format(len(templates)))

kv = KeyValues()
kv.load(sys.argv[1])
scanForInvalidTemplates(kv,sys.argv[1],['WaveSchedule'])

log.info('Finished scanning: {0} warnings, {1} errors.'.format(stats['warnings'],stats['errors']))

exportTemplates('PARSED_TEMPLATES.pop')
exportPopfile(kv,sys.argv[1]+'.new')