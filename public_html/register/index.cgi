#!/usr/bin/python

import os, sys, cgi, time, subprocess
import traceback

print "Content-type: text/html\n\n\n"
print


form = cgi.FieldStorage()
try:
    cmd = form['cmd'].value
except Exception, e:
    print '<pre>'
    print cgi.escape(repr(traceback.format_exc()))
    print '</pre>'
    cmd = None

if not cmd:
    print """
    <h2> Register new user </h2>
    <form method='post'>
	<input type='hidden' value='registerUser' name='cmd'/>
	Username: 
	<input type='text' value='Username' name='user' />
	<br/>
	New password:
	<input type='password' name='password' />
	<br/>
	Repeat password:
	<input type='password' name='password2' />
	<input type='submit' value='Submit' />
    </form>
"""

elif cmd == 'registerUser':
    changeUser = form['user'].value
    changePassword = form['password'].value
    password2 = form['password2'].value
    changePassword = changePassword.replace('\\', '\\\\')
    changePassword = changePassword.replace('"', '\\"')
    changePassword = changePassword.replace(';', '\\;')
    changePassword = changePassword.replace('|', '\\|')
    changePassword = changePassword.replace(' ','\\ ')

    if changePassword == password2:
	try:
	    print "<pre>%s</pre>"%subprocess.check_output(
		    'htpasswd -b .htpasswd.requests %s %s' % ( 
			changeUser, changePassword), shell=True)
	except:
	    print "an error occured. The admin has been notified -- Many apologies"
	    with open('../errors', 'a') as f:
		f.write(('-'*80)+'\n')
		f.write(time.strftime("%F %H:%M:%S"))
		f.write('\n')
		f.write(traceback.format_exc())
		f.write(('-'*80)+'\n')
	finally:
	    print "Registration complate"
	    print "You will receive confirmation shortly"

    else:
	print "Passwords do not match"
