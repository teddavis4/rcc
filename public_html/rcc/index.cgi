#!/usr/bin/python

import os, sys, time, cgi, cgitb, subprocess, traceback, crypt
from jinja2 import Template

cgitb.enable()

print "Content-type: text/html"
print
print

user = os.environ['REMOTE_USER']
qstring = os.environ['QUERY_STRING']

template = Template(file('main.html', 'r').read())
print str(template.render(user=user))

def getGamelist(exp=False):
    gamelist = {}
    with open('gamelist.txt') as f:
	for i in f:
	    opp = i.split(';')[0]
	    date = i.split(';')[1].strip()
	    if not exp:
		gamelist[opp] = date
	    else:
		form = "%m/%d/%y %H:%M"
		edate = time.mktime(time.strptime(date, form))
		if time.time() < edate:
		    gamelist[opp] = date
		    continue
    return gamelist

if qstring == 'vote':
    template = Template(file('vote.html', 'r').read())
    gamelist = {}
    print str(template.render(games=getGamelist(exp=True)))
if qstring == 'submitVote':
    voteTime = time.time()
    form = cgi.FieldStorage()
    if "ku" not in form or "opp" not in form:
	print "Please enter a value for both teams scores"
    if "ku" in form and "opp" in form:
	opp = form['opp'].value
	ku = form['ku'].value
	game = form['game'].value
	if ku == '0' or opp == '0':
	    print "<p>Please enter scores over 0"
	else:
	    team = False
	    index = 0
	    with open('scores', 'r') as f:
		lines = f.readlines()
	    for line in lines:
		lineNum = lines.index(line)
		newScore = False
		if line.startswith('[%s]' % game):
		    team = True
		elif line.startswith(user) and team:
			newScore = True
			lines[lineNum] = "%s:%s,%s\n" % (user, ku,
				opp)
			break
		elif line[0] == '[' and team:
		    if not newScore:
			lines.insert(lineNum, '%s:%s,%s\n'%(user, ku,
			    opp))
			break
	    with open('scores', 'w') as f:
		for line in lines:
		    f.write("%s" % line)
	    print "Scores collected, thank you"

if qstring == 'standings':
    template = Template(file('standings.html', 'r').read())
    print str(template.render(gamelist=getGamelist()))

if qstring == 'viewStandings':
    form = cgi.FieldStorage()
    game = form['game'].value
    team = False
    team = None
    kuActual = None
    oppActual = None
    kuGuess = None
    oppGuess = None
    tempVars = {'user': user, 'game': game}

    with open('actualScores.txt', 'r') as f:
	for line in f.readlines():
	    line = line.split(':')
	    team = line[0]
	    if team == game:
		tempVars['kuActual'] = int(line[1].split(',')[0])
		tempVars['oppActual'] = int(line[1].split(',')[1])
    tempVars['diff'] = abs(tempVars['kuActual'] - tempVars['oppActual'])
    with open('scores', 'r') as f:
	lines = f.readlines()
	players = {}
	for line in lines:
	    if line.startswith('[%s]'%game):
		team = True
	    elif line.startswith('['):
		team = False
	    elif team == True:
		nline = line.split(':')
		player = nline[0]
		players[player] = {}
		players[player]['kuGuess'] = int(nline[1].split(',')[0])
		players[player]['oppGuess'] = int(nline[1].split(',')[1])
		players[player]['diff'] = \
			abs(players[player]['kuGuess'] \
			- players[player]['oppGuess'])
		players[player]['adjScore'] = ( \
			100 \
			- abs( \
			(tempVars['kuActual'] + tempVars['oppActual']) \
			- (players[player]['kuGuess'] + players[player]['oppGuess']) \
			) \
			- abs(tempVars['diff'] + players[player]['diff']) \
			)
	    tempVars['players'] = players

    template = Template(file('viewStandings.html', 'r').read())
    print str(template.render(**tempVars))

if qstring == 'admin' and (user == 'ddavis' or user == 'tdavis'):
    form = cgi.FieldStorage()

    try:
	cmd = form['cmd'].value
    except Exception, e:
	cmd = 'MAIN'

    if cmd == 'registerUser':
	changeUser = form['user'].value
	changePassword = form['pssword'].value
	changePassword = changePassword.replace('"', '\\"')
	changePassword = changePassword.replace(';', '\\;')
	changePassword = changePassword.replace('|', '\\|')
	changePassword = changePassword.replace(' ','\\ ')

	try:
	    print "<pre>%s</pre>"%subprocess.check_output('htpasswd -b .htpasswd %s %s' % ( changeUser, changePassword), shell=True)
	except:
	    print "<pre>%s</pre>"%cgi.escape(traceback.format_exc())
	finally:
	    print "Password Changed"

    if cmd == 'changePassword':
	changeUser = form['changeUser'].value
	changePassword = form['changePassword'].value
	changePassword = changePassword.replace('"', '\\"')
	changePassword = changePassword.replace(';', '\\;')
	changePassword = changePassword.replace('|', '\\|')
	changePassword = changePassword.replace(' ','\\ ')

	try:
	    print "<pre>%s</pre>"%subprocess.check_output('htpasswd -b .htpasswd %s %s' % ( changeUser, changePassword), shell=True)
	except:
	    print "<pre>%s</pre>"%cgi.escape(traceback.format_exc())
	finally:
	    print "Password Changed"

    if cmd == 'enterScores':
	ku = form['ku'].value
	opp = form['opp'].value
	game = form['game'].value
	with open('actualScores.txt', 'r') as f:
	    lines = f.readlines()
	for line in lines:
	    lineNum = lines.index(line)
	    game = game.split()[0]
	    if line.startswith(game):
		lines[lineNum] = "%s:%s,%s\n" % (game, ku, opp)
		break
	with open('actualScores.txt', 'w') as f:
	    for line in lines:
		f.write("%s" % line)
	print "Scores collected, thank you"
	
    if cmd == 'changeScores':
	changeUser = form['user'].value
	ku = form['ku'].value
	opp = form['opp'].value
	game = form['game'].value
	team = False
	with open('scores', 'r') as f:
	    lines = f.readlines()
	for line in lines:
	    lineNum = lines.index(line)
	    newScore = False
	    game = game.split()[0]
	    if line.startswith('[%s]' % game):
		team = True
	    elif line.startswith(user) and team:
		newScore = True
		lines[lineNum] = "%s:%s,%s\n" % (changeUser, ku,
			opp)
		break
	    elif line[0] == '[' and team:
		if not newScore:
		    lines.insert(lineNum, '%s:%s,%s\n'%(changeUser, ku,
			opp))
		    break
	with open('scores', 'w') as f:
	    for line in lines:
		f.write("%s" % line)
	print "Scores collected, thank you"
    template = Template(file('admin.html', 'r').read())
    userlist = []
    with open('../.htpasswd', 'r') as f:
	for user in f.readlines():
	    userlist.append(user.split(':')[0])
    print str(template.render(gamelist=getGamelist(), userlist=userlist))
