#!/usr/bin/python

import cgitb
cgitb.enable(0, '/home/tdavis/python_logs')

import os, sys, cgi, time, subprocess

import traceback, psycopg2

print "Content-type: text/html\n\n\n"
print


form = cgi.FieldStorage()
try:
    cmd = form['cmd'].value
except Exception, e:
    cmd = None

if not cmd:
    print """
    <h2> Register new user </h2>
    <form method='post'>
	<input type='hidden' value='registerUser' name='cmd'/>
	Full Name: 
	<input type='text' value='' name='fullname' />
	<br/>
	Email Address:
	<input type='text' value='' name='email' />
	<br/>
	Stree address:
	<input type='text' value='' name='street' />
	<br/>
	City:
	<input type='text' value='' name='city' />
	<br/>
	State:
	<input type='text' value='' name='state' />
	<br/>
	Zip code:
	<input type='text' value='' name='zipcode' />
	<br/>
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
    try:
	changeUser = form['user'].value
	changePassword = form['password'].value
	password2 = form['password2'].value
	emailAddress = form['email'].value
	fullName = form['fullname'].value
	street = form['street'].value
	city = form['city'].value
	state = form['state'].value
	zipcode = form['zipcode'].value
    except Exception, e:
	print ("There was an error with the form data. Please make sure every "
		"field has been filled out")
    else:
	changePassword = changePassword.replace('\\', '\\\\')
	changePassword = changePassword.replace('"', '\\"')
	changePassword = changePassword.replace(';', '\\;')
	changePassword = changePassword.replace('|', '\\|')
	changePassword = changePassword.replace(' ','\\ ')

	if changePassword == password2:
	    try:
		address = "%s, %s, %s %s" % (street, city, state, zipcode)
		htpasswd = subprocess.check_output( 'htpasswd -nb %s %s' % 
			( changeUser, changePassword), shell=True)
		conn = psycopg2.connect("dbname=rcc user=tdavis "
			"password=madman12 host=127.0.0.1")
		cur = conn.cursor()
		cur.execute("""INSERT INTO testrequests (name, email, username, 
			htpasswd, address) VALUES (%s, %s, %s, %s, %s);""", 
			(fullName, emailAddress, changeUser, htpasswd, address))
		cur.close()
		conn.commit()
		conn.close()
		print "Registration complate"
		print "You will receive confirmation shortly"
		print "<br/>"
		print "<a href='/'> Home</a?"
	    except:
		print "an error occured. The admin has been notified -- Many apologies"
		with open('/usr/share/rcc/errors', 'a') as f:
		    f.write(('-'*80)+'\n')
		    f.write(time.strftime("%F %H:%M:%S"))
		    f.write('\n')
		    f.write(traceback.format_exc())
		    f.write(('-'*80)+'\n')

	else:
	    print "Passwords do not match"
