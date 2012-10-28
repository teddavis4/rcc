#!/usr/bin/python

import os, sys, time, cgi, cgitb, subprocess, traceback, crypt
from jinja2 import Template

adminList = ['tdavis', 'ddavis']

userlist = []
# find active players
with open('../.htpasswd', 'r') as f:
    for u in f.readlines():
	userlist.append(u.split(':')[0])
del u, f

def getGamelist(exp=False, over=False):
    """
    Return a list of games with their dates and times

    exp -- If set to true, skips games that have passed (False)
    over -- If set to true, only adds games which 4 hours have elapsed
	    since their start
    """

    gamelist = []
    with open('/usr/share/rcc/.gamelist.test') as f:
	for i in f:
	    opp = i.split(';')[0]
	    date = i.split(';')[1]
	    if not exp and not over:
		gamelist.append('%s - %s'%(opp, date))
	    elif exp:
		form = "%m/%d/%y %H:%M\n"
		edate = time.mktime(time.strptime(date, form))
		if time.time() < edate:
		    gamelist.append('%s - %s'%(opp, date))
	    elif over:
		form = "%m/%d/%y %H:%M\n"
		edate = time.mktime(time.strptime(date, form))
		edate += (3600*4)
		if time.time() > edate:
		    gamelist.append('%s - %s'%(opp, date))

    return gamelist

def getUserlist(new=False):
    # Find playings requesting access
    userFile = '.players'
    if new:
	userFile = '.players.request'
    newusers = {}
    with open(os.path.join('/usr/share/rcc/', userFile), 'r') as f:
	newuser = None
	for line in f:
	    if line.startswith('['):
		newuser = line.strip('[]\n')
		newusers[newuser] = {}
	    elif line.startswith('Email Address') and newuser:
		newusers[newuser]['email'] = line.split(':')[1].rstrip()
	    elif line.startswith('Mailing Address') and newuser:
		newusers[newuser]['address'] = []
	    elif line.startswith('\t'):
		try:
		    newusers[newuser]['address'].append(line.strip()) 
		except Exception, e:
		    pass
    return newusers

def getMOTD():
    with open('/usr/share/rcc/motd', 'r') as f:
	return f.read()

def render_vote(user):
    template = Template(file('vote.html', 'r').read())
    gamelist = {}
    print str(template.render(games=getGamelist(exp=True)))

def render_submitVote(user):
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
	    with open('/usr/share/rcc/.scores.test', 'r') as f:
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
	    with open('/usr/share/rcc/.scores.test', 'w') as f:
		for line in lines:
		    f.write("%s" % line)
	    print "Scores collected, thank you"

def render_standings(user):
    template = Template(file('standings.html', 'r').read())
    print str(template.render(gamelist=getGamelist(over=True)))

def render_viewStandings(user):
    form = cgi.FieldStorage()
    game = form['game'].value
    team = None
    kuActual = None
    oppActual = None
    kuGuess = None
    oppGuess = None
    tempVars = {'user': user, 'game': game}

    with open('/usr/share/rcc/.actualScores.txt', 'r') as f:
	for line in f.readlines():
	    line = line.split(':')
	    team = line[0]
	    if team == game:
		tempVars['kuActual'] = int(line[1].split(',')[0])
		tempVars['oppActual'] = int(line[1].split(',')[1])
    tempVars['diff'] = abs(tempVars['kuActual'] - tempVars['oppActual'])
    with open('/usr/share/rcc/.scores.test', 'r') as f:
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

def render_prefs(user):
    form =cgi.FieldStorage()
    template = Template(open('prefs.html', 'r').read())
    print str(template.render())

    try:
	cmd = form['cmd'].value
    except Exception, e:
	cmd = 'MAIN'
    if cmd == 'changePassword':
	changeUser = user
	changePassword = form['changePassword'].value
	password2 = form['password2'].value
	changePassword = changePassword.replace('"', '\\"')
	changePassword = changePassword.replace(';', '\\;')
	changePassword = changePassword.replace('|', '\\|')
	changePassword = changePassword.replace(' ','\\ ')

	if changePassword == password2:
	    try:
		subprocess.check_call('htpasswd -b /home/thedav4/mooksinboots.com/.htpasswd %s %s' % ( changeUser, changePassword), shell=True)
		print "Password Changed"
	    except:
		print "<pre>%s</pre>"%(cgi.escape(traceback.format_exc()))
	else:
	    print "Passwords did not match"

def render_admin(user):
    if user in adminList:
	form = cgi.FieldStorage()

	try:
	    cmd = form['cmd'].value
	except Exception, e:
	    cmd = 'MAIN'

	if cmd == 'registerUser':
	    upgrade = []
	    keepers = []
	    users = form['newuser']
	    try:
		if len(users)>1:
		    pass
		else:
		    users = [form['newuesr']]
	    except Exception, e:
		users = [form['newuser']]
	    for u in users:
		newuser = u.value
		with open('/usr/share/rcc/.htpasswd.requests', 'r') as f:
		    for line in f:
			keepers.append(line)
			if line.startswith('%s:'%newuser):
			    if newuser not in upgrade:
				upgrade.append(line)

		with open('../.htpasswd', 'a') as f:
		    for newuser in upgrade:
			if newuser not in userlist:
			    f.write(newuser)
	    keepers = [i for i in keepers if i not in upgrade]
	    with open('/usr/share/rcc/.htpasswd.requests', 'w') as f:
		for u in keepers:
		    f.write(u)
	    with open('/usr/share/rcc/.players.request', 'r') as f:
		gather=True
		keepline = []
		moveline = []
		for line in f:
		    if line.startswith('['):
			if line.strip('[]\n') == newuser:
			    gather=False
			if line.strip('[]\n') != newuser:
			    gather=True
		    if gather:
			keepline.append(line)
		    else:
			moveline.append(line)
	    with open('/usr/share/rcc/.players.request', 'w') as f:
		for i in keepline:
		    f.write(i)
	    with open('/usr/share/rcc/.players', 'a') as f:
		for i in moveline:
		    f.write(i)

	if cmd == 'changePassword':
	    changeUser = form['cuser'].value
	    changePassword = form['changePassword'].value
	    changePassword = changePassword.replace('"', '\\"')
	    changePassword = changePassword.replace(';', '\\;')
	    changePassword = changePassword.replace('|', '\\|')
	    changePassword = changePassword.replace(' ','\\ ')

	    try:
		subprocess.check_call('htpasswd -b /home/thedav4/mooksinboots.com/.htpasswd %s %s' % ( changeUser, changePassword), shell=True)
		print "Password Changed"
	    except:
		print "<pre>%s</pre>"%(cgi.escape(traceback.format_exc()))

	if cmd == 'enterScores':
	    ku = form['ku'].value
	    opp = form['opp'].value
	    game = form['game'].value
	    with open('/usr/share/rcc/.actualScores.txt', 'r') as f:
		lines = f.readlines()
	    for line in lines:
		lineNum = lines.index(line)
		game = game.split()[0]
		if line.startswith(game):
		    lines[lineNum] = "%s:%s,%s\n" % (game, ku, opp)
		    break
	    with open('/usr/share/rcc/.actualScores.txt', 'w') as f:
		for line in lines:
		    f.write("%s" % line)
	    print "Scores collected, thank you"
	    
	if cmd == 'changeScores':
	    changeUser = form['user'].value
	    ku = form['ku'].value
	    opp = form['opp'].value
	    game = form['game'].value
	    team = False
	    with open('/usr/share/rcc/.scores.test', 'r') as f:
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
	    with open('/usr/share/rcc/.scores.test', 'w') as f:
		for line in lines:
		    f.write("%s" % line)
	    print "Scores collected, thank you"
	if cmd == 'writeMOTD':
	    newMotd = form['motd'].value
	    with open('/usr/share/rcc/motd', 'w') as f:
		for line in newMotd.split('\n'):
		    f.write(line)
	template = Template(file('admin.html', 'r').read())
		

	print str(template.render(gamelist=getGamelist(),
	    userlist=userlist, newusers=getUserlist(new=True),
	    motd=getMOTD()))

def render_userlist(user):
    template = Template(file('players.html', 'r').read())
    print str(template.render(players=getUserlist()))

def render_(user):
    pass

def deliverContent(qstring, user):
    exec('render_%s(user)' % qstring)
