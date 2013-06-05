import os,sys,logging as log
from keyvalues import KeyValues

templates = {}
name2template={}
template_uses = {}
stats={
	'warnings':0,
	'errors':0
}
def importTemplates(file):
	_kv = KeyValues()
	log.info("Loading {0}".format(file))
	_kv.load(file)
	for id in _kv['Templates']:
		templates[id]=_kv['Templates'][id]
		if 'Name' in templates[id]:
			name=templates[id]['Name']
			if 'Name' not in name2template:
				name2template[name]=id
			else:
				if type(name2template[name]) is list:
					name2template[name].append(id)
				else:
					name2template[name]=[name2template[name],id]

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
	skipped=[]
	for id in templates:
		if id in template_uses:
			kv['Templates'][id]=templates[id]
			#kv['Templates'][id]['UsedTimes']=template_uses[id]
		else:
			if id in kv['Templates']:
				del(kv['Templates'][id])
			skipped.append(id)
	kv.save(file)
	log.info("Saved {0} templates to {1} ({2} skipped).".format(len(kv['Templates']),file,len(skipped)))

def checkForValueDuplication(current,template,file,cwd):
	for key in current:
		if key in template and template[key]==current[key]:
			del(current[key])
			log.warning('{0} > {1}:  Node duplicates value {2}, removing.'.format(file,cwd,repr(template[key])))
	return current

def scanForInvalidTemplates(kv,file,path):
	if type(kv) is list:
		for i in range(len(kv)):
			value = kv[i]
			cwdp=path[:]
			cwdp[-1]=path[-1]+'[{0}]'.format(i)
			cwd = '/'.join(cwdp)
			#print(cwd)
			#print((' '*(len(cwdp)+1))+' [{0}] = {1}'.format(i,type(value)))
			if type(value) is list or type(value) is KeyValues:
				kv[i]=scanForInvalidTemplates(value,file,cwdp)
				continue
		return kv
	for key in kv:
		if key not in kv:
			continue
		value=kv[key]
		cwdp = path+[key]
		#print((' '*len(cwdp))+' {0} = {1}'.format(key,type(value)))
		cwd = '/'.join(cwdp)
		if type(value) is list or type(value) is KeyValues:
			kv[key]=scanForInvalidTemplates(value,file,cwdp)
			continue
		if key == 'Template':
			if value not in templates:
				log.warning('{0} > {1}:  Unable to find Template "{2}"!'.format(file,cwd,value))
				stats['warnings']+=1
			if cwdp[-2].split('[')[0] != 'TFBot':
				log.warning('{0} > {1}:  Template directive contained in "{2}" instead of TFBot!'.format(file,cwd,cwdp[-2].split('[')[0]))
				stats['warnings']+=1
			if value not in template_uses:
				template_uses[value]=1
			else:
				template_uses[value]+=1
			# Check to see if values match parent
			kv=checkForValueDuplication(kv,templates[value],file,cwd)
			
		if cwdp[-2].split('[')[0] == 'TFBot':
			if key == 'Name':
				if value in name2template:
					if type(name2template[value]) is not list:
						log.warning('{0} > {1}:  TFBot named "{2}" might needs Template "{3}"! This has automatically been done for you.'.format(file,cwd,value,name2template[value]))
						kv['Template']=name2template[value]
						kv._children.move_to_end('Template',last=False)
						
						# Check to see if values match parent
						kv=checkForValueDuplication(kv,templates[name2template[value]],file,cwd)
					else:
						log.warning('{0} > {1}:  TFBot named "{2}" might need a Template from any of the following examples:'.format(file,cwd,value))
						for tplID in name2template[value]:
							log.info('  Template "{0}"'.format(tplID))
					stats['warnings']+=1
	return kv

log.basicConfig(format='%(asctime)s [%(levelname)-8s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename=sys.argv[1]+'.log',filemode='w',level=log.DEBUG)

importTemplates('includes/robot_standard.pop')
importTemplates('includes/robot_giant.pop')

kv = KeyValues()
kv.load(sys.argv[1])
if 'Templates' in kv:
	for id in kv['Templates']:
		templates[id]=kv['Templates'][id]
log.info('Loaded {0} templates.'.format(len(templates)))
scanForInvalidTemplates(kv,sys.argv[1],['WaveSchedule'])

log.info('Finished scanning: {0} warnings, {1} errors.'.format(stats['warnings'],stats['errors']))

log.info('Used templates: {0}'.format(len(template_uses)))
for key in template_uses:
	log.info('Template {0}: Used {1} times.'.format(key,template_uses[key]))

exportTemplates('PARSED_TEMPLATES.pop')
exportPopfile(kv,sys.argv[1]+'.new')