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
import argparse
from keyvalues import KeyValues

# Everything not alphanumeric will match this.
# The + at the end means it'll match an entire block of such characters 
#  instead of singular instances.
REGEX_INVALID_TEMPLATE_KEY_CHARS=re.compile(r'[^a-zA-Z0-9]+')

# Valid Keys.
ValidKeys = [
	'Action',
	'Advanced',
	'Attributes',
	'BeginAtWave',
	'BehaviorModifiers',
	'CanBotsAttackWhileInSpawnRoom',
	'CharacterAttributes',
	'Checkpoint',
	'Class',
	'ClassIcon',
	'CooldownTime',
	'DesiredCount',
	'DoneOutput',
	'Health',
	'InitialCooldown',
	'Item',
	'MaxActive',
	'MaxVisionRange',
	'Mission',
	'Name',
	'Objective',
	'OnBombDroppedOutput',
	'RandomChoice',
	'RespawnWaveTime',
	'RunForThisManyWaves',
	'Scale',
	'Skill',
	'Skin',
	'Sound',
	'SpawnCount',
	'Speed',
	'Squad',
	'StartingCurrency',
	'StartingPathTrackNode',
	'StartWaveOutput',
	'Support',
	'Tank',
	'Target',
	'TeleportWhere',
	'Template',
	'Templates',
	'TFBot',
	'TotalCount',
	'TotalCurrency',
	'WaitBeforeStarting',
	'WaitBetweenSpawns',
	'WaitForAllSpawned',
	'WaitWhenDone',
	'Wave',
	'WaveSchedule',
	'WaveSpawn',
	'WeaponRestrictions',
	'Where',
]

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

# Duh.  Used for Where validation.
ValidSpawns=[
	# These ones are virtual.
	'BEHIND',
	'AHEAD'
]

# Load up our #base include
def importTemplates(file):
	_kv = KeyValues()
	log.info("Loading {0}".format(file))
	_kv.load(file)
	for id in _kv['Templates']:
		importTemplate(id,_kv['Templates'][id])

def importSpawnPoints(file):
	with open(file,'r') as f:
		log.info('Valid spawns loaded:')
		for line in f:
			line=line.strip()
			ValidSpawns.append(line)
			log.info('  '+line)

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
	new_kv = KeyValues("Templates")
	for id in sorted(templates):
		if id in template_uses:
			new_kv[id]=templates[id]
			new_kv.set_comment(id,'Used {0} times'.format(template_uses[id]),0)
		else:
			skipped.append(id)
	kv['Templates']=new_kv
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
		parent=cwdp[-2]
		#print((' '*len(cwdp))+' {0} = {1}'.format(key,type(value)))
		cwd = '/'.join(cwdp)
		if key not in ValidKeys:
			if parent not in ['Templates','CharacterAttributes']:
				foundCorrectCase=False
				for vkey in ValidKeys:
					if vkey.lower() == key.lower():
						log.warning('{0} > {1}:  Key "{2}" has bad capitalization! The correct form is "{3}".'.format(file,cwd,key,vkey))
						stats['warnings']+=1
						foundCorrectCase=True
						temp = kv[key]
						del kv[key]
						kv[vkey] = temp
						key=vkey
						break
				if not foundCorrectCase:
					log.warning('{0} > {1}:  Unidentified key "{2}"!'.format(file,cwd,key))
					stats['warnings']+=1
		if type(value) is list or type(value) is KeyValues:
			kv[key]=scanForInvalidTemplates(value,file,cwdp)
			if type(value) is list:
				if key == 'Wave':
					#print(repr(value))
					for i in range(len(value)):
						kv.set_comment_list(key,i,'Wave {0}'.format(i+1),1)
				if key == 'WaveSpawn' and cwdp[-2].split('[')[0] == 'Wave':
					parentWaveNumber = cwdp[-2].split('[')[1].strip(']')
					parentWaveNumber = int(parentWaveNumber)
					if type(value) is list:
						for i in range(len(value)):
							kv.set_comment_list(key,i,'Wave {0}.{1}'.format(parentWaveNumber+1,i+1),1)
					elif type(value) is KeyValues:
						kv.set_comment(key,'Wave {0}.{1}'.format(parentWaveNumber+1,1),1)
			continue
		if key == 'Where':
			if value not in ValidSpawns:
				log.warning('{0} > {1}:  Spawnpoint "{2}" not defined on the map!'.format(file,cwd,value))
				stats['warnings']+=1
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
			if value in templates:
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
	
#importTemplates('includes/robot_standard.pop')
#importTemplates('includes/robot_giant.pop')

parser = argparse.ArgumentParser(description='Clean up and optimize TF2 MvM Popfiles')

# -o --output Specify output file
parser.add_argument('-o', '--output', nargs='?', default='', help='Specify where the completed file should go')
# -i --include Include templates from a file
parser.add_argument('-i', '--include', nargs='*', default=['includes/robot_giant.pop','includes/robot_standard.pop'], help='Include templates from a file')
# -s --spawnpoints Load valid spawnpoint targetnames from a file
parser.add_argument('-s', '--spawnpoints', nargs='?', default='', help='Load valid spawnpoint targetnames from a file')
parser.add_argument('input_file', nargs=1, help='The popfile to be processed.')

args  = parser.parse_args()

outfile = args.output
if outfile == '':
	outfile=args.input_file+'.new'
outfile = os.path.abspath(outfile)
outdir = os.path.dirname(outfile)
if not os.path.isdir(outdir):
	os.makedirs(outdir)

log.basicConfig(format='%(asctime)s [%(levelname)-8s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename=outfile+'.log',filemode='w',level=log.DEBUG)

for included_file in args.include:
	importTemplates(included_file)

if args.spawnpoints != '':
	importSpawnPoints(args.spawnpoints)

kv = KeyValues()
kv.load(sys.argv[1])
if 'Templates' in kv:
	for id in kv['Templates']:
		templates[id]=kv['Templates'][id]
log.info('Loaded {0} templates.'.format(len(templates)))

scanForInvalidTemplates(kv,args.input_file,['WaveSchedule'])

log.info('Finished scanning: {0} warnings, {1} errors.'.format(stats['warnings'],stats['errors']))

log.info('Used templates: {0}'.format(len(template_uses)))
for key in sorted(template_uses.keys()):
	log.info('Template {0}: Used {1} times.'.format(key,template_uses[key]))

#exportTemplates('PARSED_TEMPLATES.pop')

exportPopfile(kv,outfile)
log.info('Exported to {0}.'.format(outfile))