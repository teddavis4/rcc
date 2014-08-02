#!/usr/bin/python

import os, sys, cgi, cgitb, subprocess, crypt, re, traceback
import cPickle as pickle
from datetime import tzinfo, timedelta, datetime
from jinja2 import Template

class User():
    def __init__(self):
	self.username = None
	self.name = None
	self.password = None
	self.email = None
	self.games 

    def SetUsername(self, username):
	if self.username:
	    raise Exception("Username has already been set.")
	self.username = username

    def SetName(self, name):
	self.name = name

    def SetPassword(self, password):
	self.password = crypt.crypt(password, 'mysecret')

    def SetEmail(self, email):
	if len(email.split('@')) == 2:
	    self.email = email
	else:
	    raise Exception("Badly formed email address")

    def EnterScores(self, date, ku, opponent):
	if datetime.now() > date:
	    raise Exception("All guessing for this game is closed")
	if ku > 0 and opponent > 0:
	    self.games[date] = (ku, opponent)
	else:
	    raise Exception("Please enter scores greater than 0")

    def SaveUser(self):
	with open("/rcc/%s.pickle"%self.username, 'w') as f:
	    self.dump(self, f)

