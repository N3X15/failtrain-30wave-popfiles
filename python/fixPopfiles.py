"""
TF2 Popfile Tidy
Copyright (c)2013 Rob "N3X15" Nelson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import os,sys,re,logging as log
from keyvalues import KeyValues

# Everything not alphanumeric will match this.
# The + at the end means it'll match an entire block of such characters 
#  instead of singular instances.
REGEX_INVALID_TEMPLATE_KEY_CHARS=re.compile(r'[^a-zA-Z0-9]+')

# Template data
templates = {}

# TFBot name -> ID associations
name2template={}

# Template usage counts
template_uses = {}

# Times a certain template name has been used
namecounts={}

# Errors and warning stats
stats={
	'warnings':0,
	'errors':0
}

# Load up our #base include
def importTemplates(file):
	_kv = KeyValues()
	log.info("Loading {0}".format(file))
	_kv.load(file)
	for id in _kv['Templates']:
		importTemplate(id,_kv['Templates'][id])

# Actually import the template
def importTemplate(id,template):
	templates[id]=template
	if 'Name' in templates[id]:
		name=templates[id]['Name']
		if 'Name' not in name2template:
			name2template[name]=id
		else:
			if type(name2template[name]) is list:
				name2template[name].append(id)
			else:
				name2template[name]=[name2template[name],id]

# Export templates to a file.
def exportTemplates(file):
	kv = KeyValues('WaveSchedule')
	log.info("Saving to {0}...".format(file))
	kv['Templates']=KeyValues('Templates')
	for id in templates:
		kv['Templates'][id]=templates[id]
	kv.save(file)
	log.info("Saved {0} templates to {1}.".format(len(templates),file))
	
# Export an entire popfile.
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
		if key in template:
			if type(current[key]) is list:
				newValue = []
				for idx in range(len(current[key])):
					value = current[key][idx]
					ckey = '{0}[{1}]'.format(key,idx)
					if type(template[key]) is list:
						if value in template[key]:
							log.warning('{0} > {1}:  Node \'{2}\' duplicates value {3}, removing.'.format(file,cwd,ckey,repr(template[key][idx])))
						else:
							newValue.append(value)
					else:
						if value == template[key]:
							log.warning('{0} > {1}:  Node \'{2}\' duplicates value {3}, removing.'.format(file,cwd,ckey,repr(template[key][idx])))
						else:
							newValue.append(value)
				if len(newValue) > 0:
					current[key]=newValue
				else:
					del(current[key])
			elif type(current[key]) is KeyValues:
				current[key]=checkForValueDuplication(current[key],template[key],file,cwd+'/'+key)
				if len(current[key])==0:
					del(current[key])
			else:
				if template[key]==current[key]:
					del(current[key])
					log.warning('{0} > {1}:  Node \'{2}\' duplicates value {3}, removing.'.format(file,cwd,key,repr(template[key])))
					
	return current
	
def duplicateOf(a,b):
	for key in a:
		if key in b:
			if type(a[key]) != type(b[key]):
				return False
			if b[key]!=a[key]:
				return False
	return True
	
def makeOptimizedTemplate(current,file,cwd):
	name = current['Name']
	if name not in namecounts:
		namecounts[name]=0
	namecounts[name]+=1
	nameToUse=''
	while True:
		#finalName=name.replace(" ","_")
		finalName=REGEX_INVALID_TEMPLATE_KEY_CHARS.sub('_',name).strip('_')
		if namecounts[name]>1:
			finalName='T_OPT_TFBot_{0}_{1}'.format(finalName,namecounts[name])
		else:
			finalName='T_OPT_TFBot_{0}'.format(finalName)
		if (finalName in templates and duplicateOf(current,templates[finalName])) or finalName not in templates:
			nameToUse=finalName
			break
		namecounts[name]+=1
	importTemplate(nameToUse,current)
	if nameToUse not in template_uses:
		template_uses[nameToUse]=1
	else:
		template_uses[nameToUse]+=1
	current=KeyValues()
	current['Template'] = nameToUse
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
			if 'Templates' in cwdp:
				print(repr(cwd))
			else:
				if cwdp[-2].split('[')[0] != 'TFBot':
					log.warning('{0} > {1}:  Template directive contained in "{2}" instead of TFBot!'.format(file,cwd,cwdp[-2].split('[')[0]))
					stats['warnings']+=1
			if value not in template_uses:
				template_uses[value]=1
			else:
				template_uses[value]+=1
			# Check to see if values match parent
			kv=checkForValueDuplication(kv,templates[value],file,cwd)
			
		if cwdp[-2].split('[')[0] == 'TFBot' or cwdp[-2] == 'Templates':
			if key == 'Name':
				if value in name2template:
					if type(name2template[value]) is not list:
						log.warning('{0} > {1}:  TFBot named "{2}" might needs Template "{3}"! This has automatically been done for you.'.format(file,cwd,value,name2template[value]))
						kv['Template']=name2template[value]
						kv._children.move_to_end('Template',last=False)
						
						# Check to see if values match parent
						fixedCwd = '/'.join(cwdp[:-1])
						kv=checkForValueDuplication(kv,templates[name2template[value]],file,fixedCwd)
						
						if name2template[value] not in template_uses:
							template_uses[name2template[value]]=1
						else:
							template_uses[name2template[value]]+=1
					else:
						log.warning('{0} > {1}:  TFBot named "{2}" might need a Template from any of the following examples:'.format(file,cwd,value))
						for tplID in name2template[value]:
							log.info('  Template "{0}"'.format(tplID))
					stats['warnings']+=1
				else:
					# Optimize
					kv = makeOptimizedTemplate(kv,file,cwd)
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
for key in sorted(template_uses.keys()):
	log.info('Template {0}: Used {1} times.'.format(key,template_uses[key]))

exportTemplates('PARSED_TEMPLATES.pop')
exportPopfile(kv,sys.argv[1]+'.new')