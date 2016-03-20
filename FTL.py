#!/usr/bin/python

import sys, argparse, time
from ev3dev import *

lmotor = large_motor(OUTPUT_A); assert lmotor.connected
rmotor = large_motor(OUTPUT_B); assert rmotor.connected

cs     = color_sensor();        assert cs.connected
ts     = touch_sensor();        assert ts.connected
ls     = light_sensor();		assert ls.connected
inf    = infrared_sensor();		assert inf.connected

cs.mode = 'COL-REFLECT'

standard_speed = 0
lmotor.speed_regulation_enabled = 'on'
rmotor.speed_regulation_enabled = 'on'

last_error = 0
integral   = 0

csv = 0
lsv = 0

#pobieranie wartosci koloru bialego
def get_white():
	i = 0
	x = 20
	white = 0
	tempcsv = 0
	#oczekiwanie na wcisniecie czujnika dotyku
	while not ts.value():
		time.sleep(0.01)
	
	#pobor 20 probek z czujnika koloru podczas jazdy przez sekunde i zsumowanie ich
	sound.speak("Start", True)
	while i < x:
		tempcsv = tempcsv + cs.value()
		rmotor.run_forever(speed_sp=250)
		lmotor.run_forever(speed_sp=250)
		i = i+1
		time.sleep(0.05)
	
	rmotor.run_forever(speed_sp=0)
	lmotor.run_forever(speed_sp=0)
	sound.speak("Stop", True)
	
	#oczekiwanie na wcisniecie czujnika dotyku
	while not ts.value():
		time.sleep(0.01)
	
	#pobor 20 probek z czujnika koloru podczas jazdy przez sekunde i zsumowanie ich
	sound.speak("Start", True)
	i = 0
	while i < x:
		tempcsv = tempcsv + cs.value()
		rmotor.run_forever(speed_sp=250)
		lmotor.run_forever(speed_sp=250)
		i = i+1
		time.sleep(0.05)

	rmotor.run_forever(speed_sp=0)
	lmotor.run_forever(speed_sp=0)
	sound.speak("Stop", True)
	
	#Obliczenie sredniej z odczytow
	white = int(tempcsv/(2*x))
	print("White: %s" %(white))

	while not ts.value():
		time.sleep(0.01)

	time.sleep(1) 
	return white

	#omijanie przeszkody
def evadeObstacle():
	
	#ustawianie sie na wprost przeszkody
	if(cs.value() - white>10):
		lmotor.run_forever(speed_sp=0)           
		rmotor.run_forever(speed_sp=100)
		time.sleep(0.01)		

	#Stop
	lmotor.run_forever(speed_sp=0)           
	rmotor.run_forever(speed_sp=0)
	time.sleep(0.05)

    #Obrot w lewo
	lmotor.run_forever(speed_sp=0)
	rmotor.run_forever(speed_sp=700)
	time.sleep(0.35)

    #Jazda prosto
	lmotor.run_forever(speed_sp=700)
	rmotor.run_forever(speed_sp=700)
	time.sleep(0.27)
	
	#Obrot w prawo
	lmotor.run_forever(speed_sp=700)
	rmotor.run_forever(speed_sp=0)
	time.sleep(0.33)
	
	#Jazda prosto
	lmotor.run_forever(speed_sp=700)
	rmotor.run_forever(speed_sp=700)
	time.sleep(0.65)

    #Obrot w prawp
	lmotor.run_forever(speed_sp=500)
	rmotor.run_forever(speed_sp=0)
	time.sleep(0.33)
	
    #Jazda prosto dopoki czujnik nie wykryje linii
	while(cs.value()>20):
		lmotor.run_forever(speed_sp=400)
		rmotor.run_forever(speed_sp=400)
	
    #Obrot w lewo
	lmotor.run_forever(speed_sp=0)
	rmotor.run_forever(speed_sp=700)
	time.sleep(0.15)

#ustawianie mocy silnikow
def calc_speed(correction, error):
	
	#im mniejszy blad, tym szybciej robot sie porusza
	if abs(error) < 5:
		standard_speed = 330
	elif abs(error) < 15:
		standard_speed = 310
	else:
		standard_speed = 290

	#ustawianie predkosci lewego kola
	speed_sp=(standard_speed+correction)
	if(speed_sp>1000):
		speed_sp=999
	elif(speed_sp<-1000):
		speed_sp=-999
	lmotor.run_forever(speed_sp=speed_sp)
	
	#ustawianie predkosci prawego kola
	speed_sp=(standard_speed-correction)
	if(speed_sp>1000):
		speed_sp=999
	elif(speed_sp<-1000):
		speed_sp=-999
	rmotor.run_forever(speed_sp=speed_sp)   
	
	return

#pobierz wartosc koloru bialego
white = get_white()

#przerywamy jazde wcisnieciem czujnika dotyku
while not ts.value():

	#odczyt wartosci czujnikow, wartosc czujnika swiatla normalizowana funkcja liniowa
	csv = cs.value()
	lsv=int((ls.value()-344.625)/5.5625)
	
	#jesli odczyt czujnika koloru wiekszy niz swiatla, skrecamy w prawo
    if csv>=lsv:
		error=white - lsv
	#jesli odczyt czujnika koloru mniejszy niz swiatla, skrecamy w lewo
    else:
		error=csv - white
	
	#obliczanie calki i pochodnej
    integral   = 0.5 * integral + error
    derivative = error - last_error
    last_error = error
	print ("csv: %s, lsv: %s, error: %s " %(csv,lsv,error))
	
	#obliczanie korekcji za pomoca regulacji PID
	correction = int (2.6 * error + 4.2 * integral + 25 * derivative)
	
	#jesli oba czujniki wykrywaja kolor czarny, jedz prosto przez skrzyzowanie
	if lsv<15 and csv<15:
		lmotor.run_forever(speed_sp=500)
		rmotor.run_forever(speed_sp=500)

	#jesli czujnik podczerwieni wykrywa przeszkode, omin ja
	elif inf.value()<11:
		evadeObstacle()
		
	#jesli nie wykryto skrzyzowan ani przeszkody, skoryguj predkosci za pomoca korekcji PID
	else:
		calc_speed(correction, error) 
        
	time.sleep(0.005)