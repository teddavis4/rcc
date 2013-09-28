#!/usr/bin/python

import os, sys, time, cgi, cgitb, subprocess, traceback, crypt
import rcclib
from jinja2 import Template

cgitb.enable(0, '/home/tdavis/python_logs')
#cgitb.enable()

print "Content-type: text/html"
print
print

try:
    user = os.environ['REMOTE_USER']
except:
    user = ''
try:
    qstring = os.environ['QUERY_STRING']
except:
    qstring = None

template = Template(file('main.html', 'r').read())
motd = rcclib.getMOTD()
if qstring:
    motd = ''
admin = False
if user in rcclib.adminList:
    admin = True

print str(template.render(user=user, admin=admin, motd=motd))

userlist = rcclib.userlist

rcclib.deliverContent(qstring, user)
