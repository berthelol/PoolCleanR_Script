# Pre requis
# Installer sur la rasp des paquets, lignes de commandes suivantes :
# sudo apt-get install python3
# sudo apt-get install python
# sudo apt-get install python3-picamera
# sudo apt-get install python-picamera
# sudo apt-get install python-pip
# sudo apt-get install python3-pip
#
#
# ip rasp pi 3 chez Berthelot : 78.194.188.148
#


# On importe le module OS qui dispose de variables et de fonction utiles pour dialoguer avec le systeme d'exploitation
from __future__ import division
import os
import requests
import json
import RPi.GPIO as GPIO
#import spidev
import time



# On active les ports GPIO
#GPIO.setmode(GPIO.BOARD) # A retirer pour les simulations sur ordi
GPIO.setmode(GPIO.BCM) # A retirer pour les simulations sur ordi
GPIO.setwarnings(False)
DEBUG = 1

#Initialisation des variables
# Les connexions a la rasp
pinMesureTemp = 2 # CH2 sur le CAN
pinMesurePh = 1 # CH1 sur le CAN
pinMesureChlore = 0 # CH0 sur le CAN
pinBacAcide = 5 # CH5 sur le CAN
pinBacBasique = 4 # CH4 sur le CAN
pinBacChlore = 6 # CH3 sur la CAN

pinLedBacAcide = 21 # Pin 21 rasp
pinLedBacBasique = 20 # Pin 20 rasp
pinLedBacChlore = 16 # Pin 16 rasp

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9 # Pin 9 Rasp
SPIMOSI = 10
SPICS = 8

# Variables globales
mode = 0
taillePiscine = 0

valTemp = 27
valPh = 7
valChlore = 1.6
valBacAcide = 1
valBacBasique = 2
valBacChlore = 3

actionBasique = 0
actionChlore = 0
actionAcide = 0

notifBacAcide = 0
notifBacBasique = 0
notifBacChlore = 0

orderBacChlore = 0
orderBacPh = 0

# FONCTIONS

# FONCTIONS INITIALISATIONS

def initialisationPin():
	#GPIO.setup(pinRecup, GPIO.IN)
	GPIO.setup(pinLedBacAcide, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(pinLedBacBasique, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(pinLedBacChlore, GPIO.OUT, initial=GPIO.LOW)

	# set up the SPI interface pins
	GPIO.setup(SPIMOSI, GPIO.OUT)
	GPIO.setup(SPIMISO, GPIO.IN)
	GPIO.setup(SPICLK, GPIO.OUT)
	GPIO.setup(SPICS, GPIO.OUT)


# FONCTIONS DE MESURES

# Fonction mesure pH
def mesurePh():
	global valPh
	global pinMesurePh
	# En attendant de connecter le programme aux capteurs on entre manuellement les valeurs
	if mode == 1:
		valPh = float(input("Entrer val pH : "))
	if mode == 2:
		valPh = float((14/1023* readadc(pinMesurePh)))
	print("PH MESURE : ",valPh)
		
# Fonction mesure chlore
def mesureChlore():
	global valChlore
	global pinMesureBacChlore
	# En attendant de connecter le programme aux capteurs on entre manuellement les valeurs ( )
	if mode == 1:
		valChlore = float(input("Entrer val chlore : "))
	if mode == 2:
		valChlore = float(3 / 1023 * readadc(pinMesureChlore))
	print("CHLORE MESURE : ",valChlore)

# Fonction mesure temperature
def mesureTemp():
	global valTemp
	global pinMesureTemp
	# En attendant de connecter le programme aux capteurs on entre manuellement les valeurs
	if mode == 1:
		valTemp = float(input("Entrer val temperature : "))
	if mode == 2:
		valTemp = float((10/1023* readadc(pinMesureTemp))+15)
	print("T MESURE : ",valTemp)
        
def mesureBacAcide():
	global valBacAcide
	global pinBacAcide
	if mode == 1:
		valBacAcide = int(input("Entrer le \% \de remplissage du bac de solution acide : "))
	if mode == 2:
		valBacAcide = int(100/1023* readadc(pinBacAcide))
		
	print("BAC ACIDE : ",valBacAcide)

def mesureBacBasique():
	global valBacBasique
	global pinBacBasique
	if mode == 1:
		valBacBasique = int(input("Entrer le \% \de remplissage du bac de solution basique : "))
	if mode == 2:
		valBacBasique = int(100/1023*readadc(pinBacBasique))
		
	print("BAC BASIQUE : ",valBacBasique)

def mesureBacChlore():
	global valBacChlore
	global pinBacChlore
	if mode == 1:
		valBacChlore = int(input("Entrer le \% \de remplissage du bac de chlore : "))
	if mode == 2:
		valBacChlore = int(100/1023*readadc(pinBacChlore))
		
	print("BAC CHLORE : ",valBacChlore)
        
def mesureBacs():
	mesureBacAcide()
	mesureBacBasique()
	mesureBacChlore()

#Fonction d'appel des fonctions effectuant les differentes mesures
def mesures():
	mesurePh()
	mesureTemp()
	mesureChlore()

# FONCTIONS DE VERIFICATION

# Fonction verification taux pH
def verifPh():
	global actionAcide
	global actionBasique
	global valPh
	global orderBacPh

	valPhAttendue = float(7.2)

	# Cas ph trop eleve
	if (valPh > 7.5 or (orderBacPh and valPh > valPhAttendue)):
		calculAcide()
		actionAcide = 1 # On note qu'une action a ete effectuer en vue de l'envoyer
	else :
		actionAcide = 0

	# Cas ph trop bas
	if (valPh < 6.9 or (orderBacPh and valPh <= valPhAttendue)):
		calculBasique()
		actionBasique = 1 # On note qu'une action a ete effectuer en vue de l'envoyer
	else :
		actionBasique = 0

	if (orderBacPh == 1):
		orderBacPh = 0
		# Delete l'ordre de la BDD

# Fonction verification taux chlore
def verifChlore():
	global actionChlore
	global valChlore
	global orderBacChlore

	valChloreAttenue = float(1.5)
	valChloreLimiteBasse = float(1.2)

	if((valChlore < valChloreLimiteBasse) or (orderBacChlore and valChlore < valChloreAttenue)):
		calculChlore(valChloreAttenue - valChlore)
		actionChlore = 1 # On note qu'une action a ete effectuer en vue de l'envoyer
	else:
		actionChlore = 0

	if(orderBacChlore == 1):
		orderBacChlore = 0
		# Delete l'ordre de la BDD

#Fonction d'appel des fonctions effectuant les differentes verif
def verifMesures():
	verifPh()
	verifChlore()

# FONCTIONS D'ACTIONS
def calculAcide():
	global valPh

	delta = valPh - 7.2 # Delta entre la val mesuree et la val attendue

	coeff = taillePiscine / 50 # Coefficiant utilise pour convertir le delta en temps d'ouverture de la trappe
	temps = delta * coeff

	if mode == 2:
		# On ouvre la trappe
		GPIO.output(pinLedBacAcide, GPIO.HIGH)
		time.sleep(temps) # Pendant 'temps' secondes
		GPIO.output(pinLedBacAcide, GPIO.LOW)
	
	print("On ouvre la trappe de l'acide pendant ",temps)

def calculBasique():
	global valPh

	delta = 7.2 - valPh
	coeff = float(taillePiscine / 50) # Coefficiant utilise pour convertir le delta en temps d'ouverture de la trappe
	temps = float(delta * coeff)

	if mode == 2:
		print(temps)
		# On ouvre la trappe
		GPIO.output(pinLedBacBasique, GPIO.HIGH)
		time.sleep(temps) # Pendant 'temps' secondes
		GPIO.output(pinLedBacBasique, GPIO.LOW)
	
	print("On ouvre la trappe du basique pendant ",temps)

def calculChlore(delta):
	coeff = taillePiscine / 20 # Coefficiant utilise pour convertir le delta en temps d'ouverture de la trappe
	temps = delta * coeff

	if mode == 2:
		# On ouvre la trappe
		GPIO.output(pinLedBacChlore, GPIO.HIGH)
		time.sleep(temps) 
		GPIO.output(pinLedBacChlore, GPIO.LOW)
	
	print("On ouvre la trappe du chlore pendant ",temps)

# FONCTION D'ENVOI
def envoiTotal():
	envoiChlore()
	envoiPh()
	envoiTemp()

def envoiChlore():
	global valChlore
	global valBacChlore
	global actionChlore

	#url = 'http://loicberthelot.freeboxos.fr/device/Chlore'
	url = 'http://localhost:3000/device/Chlore'

	if actionChlore == 1  :
		flag = "true"
	else :
		flag = "false"

	data = {
		"mesure": float(valChlore),
		"bac":
		{
		   "flag":flag,
		   "remplissage": int(valBacChlore)
		}
	}

	response = requests.post(url, json = data)
	print("ENVOI DATA CHLORE\nStatus:")
	print(response.status_code)
	print("Response body:")
	print(response.text)

def envoiPh():
	global valPh
	global valBacAcide
	global actionAcide
	global valBacBasique
	global actionBasique

	url = 'http://localhost:3000/device/pH'

	if actionAcide == 1  :
		flagAcide = "true"
	else :
		flagAcide = "false"

	if actionBasique == 1  :
		flagBasique = "true"
	else :
		flagBasique = "false"

	data = {
		"mesure": float(valPh),
		"bac":
		{
		   "bacmoins": {
		   "flag":flagAcide,
		   "remplissage":valBacAcide
		   },
		   "bacplus":{
		   "flag":flagBasique,
		   "remplissage":valBacBasique
		   }
		}
	}

	response = requests.post(url, json = data)
	print("ENVOI DATA PH\nStatus:",response.status_code)
	print("Response body:",response.text)

def envoiTemp():
	global valTemp

	url = 'http://localhost:3000/device/Temperature'

	data = {
		"mesure":valTemp
	}

	response = requests.post(url, json = data)
	print("ENVOI DATA TEMPERATURE\nStatus:")
	print(response.status_code)
	print("Response body:")
	print(response.text)

# RECUPERATION DES DONNEES DU SERVER
# Recuperation Taille Piscine
def getTaillePiscine():
	url = 'http://localhost:3000/user/pool/'

	response = requests.get(url)
	data = json.loads(response.text)

	return data['size']

# Recuperation des ordres de mesure (bacs)
def getOrdre():
	global orderBacChlore
	global orderBacPh
	url = 'http://localhost:3000/order'

	response = requests.get(url)

	if(response.status_code == 200):
		data = json.loads(response.text)

		# On recupere l'identifiant de l'ordre
		i = data['_id']

		# Cas MAJ Chlore
		if (data['ordername'] == 'openbacchlore'): 
			orderBacChlore = 1
			print("Ordre Chlore recu")
			verifChlore()

		if (data['ordername'] == 'openbacph'): # Cas MAJ PH
			orderBacPh = 1
			print("Ordre PH recu")
			verifPh()

		# Une fois l'ordre traite on le supprime de la BDD
		data = {
			'orderid': i,
		}

		respoonse = requests.delete(url, json = data)
		print("EFFACE ORDER BDD :\n",response)


# FONCTION DE LECTURE DES POTENTIOMETRES (DONC DU CAN)
#fonction lisant les donnees SPI de la puce MCP3008,
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
	clockpin = SPICLK
	mosipin = SPIMOSI
	misopin = SPIMISO
	cspin = SPICS

    	if ((adcnum > 7) or (adcnum < 0)):
		return -1
   	 
	GPIO.output(cspin, True)
 
    	GPIO.output(clockpin, False)  # start clock low
    	GPIO.output(cspin, False)     # bring CS low
 
    	commandout = adcnum
    	commandout |= 0x18  # start bit + single-ended bit
    	commandout <<= 3    # we only need to send 5 bits here
    	for i in range(5):
        	if (commandout & 0x80):
            		GPIO.output(mosipin, True)
        	else:
            		GPIO.output(mosipin, False)
        	commandout <<= 1
        	GPIO.output(clockpin, True)
        	GPIO.output(clockpin, False)
 
    	adcout = 0
    	# read in one empty bit, one null bit and 10 ADC bits
    	for i in range(12):
        	GPIO.output(clockpin, True)
        	GPIO.output(clockpin, False)
        	adcout <<= 1
        	if (GPIO.input(misopin)):
            		adcout |= 0x1
 
    	GPIO.output(cspin, True)
        
    	adcout >>= 1       # first bit is 'null' so drop it
    	return adcout

# FONCTION DE TEST

def choixMode():
	global mode
	print("Choisir le mode :")
	print("1 - Manuel (entree des valeurs au clavier)")
	mode = int(input("2 - Automatique (mesure des valeurs par capteurs\n"))
	if mode<1 or mode>2:
		print("Erreur d'entree")
		mode=0

# BOUCLE (main)

# Boucle de fonctionnement
taillePiscine = 0
mode = 0
tempsTraitement = time.time()-30 # pour y rentrer des le debut
tempsGet = tempsTraitement
initialisationPin() # Ne fonctionne pas lorsqu'on test sur ordi
while 1 :
	while mode == 0:
		choixMode()

	while taillePiscine ==0:
		taillePiscine = getTaillePiscine()
		print("Taille piscine lue : ")
		print(taillePiscine)
	while 1 :
		if (time.time() - tempsTraitement) >= 10 : # valeur correspondant a la duree d'attente entre chaque mesure (en secondes)
			mesureBacs()
			mesures()
			verifMesures()
			envoiTotal()
			tempsTraitement = time.time() # Temps en seconde
			print('TIME : ',tempsTraitement)	
			# Si on veut avoir un break a chaque tour de boucle	
			#i = int(input("Wesh ! "))

		if(time.time() - tempsGet >= 5):
			getOrdre()
			tempsGet = time.time()


