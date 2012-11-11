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
userlist.sort()

def getDateEpoch(inDate):
    form = "%m/%d/%y %H:%M"
    date = time.mktime(time.strptime(inDate, form))
    return date


def getGamelist(exp=False, over=False, gameOnly=False, gsplit=False):
    """
    Return a list of games with their dates and times

    exp -- If set to true, skips games that have passed (False)
    over -- If set to true, only adds games which 4 hours have elapsed
	    since their start
    gameOnly -- Only return the games, no times or dates
    gsplit -- Split the opposing team and time into a dictionary
    """

    gamelist = []
    if gsplit:
	gamelist = {}
    with open('/usr/share/rcc/.gamelist.txt') as f:
	for i in f:
	    opp = i.split(';')[0].strip()
	    rdate = i.split(';')[1].strip()
	    date = " - %s" % rdate
	    if gameOnly:
		date = ''
	    if exp:
		edate = getDateEpoch(rdate)
		if time.time() < edate:
		    gamelist.append('%s%s'%(opp, date))
	    elif over:
		edate = getDateEpoch(rdate)
		edate += (3600*4)
		if time.time() > edate:
		    gamelist.append('%s%s'%(opp, date))
	    elif gsplit:
		gamelist[rdate] = opp
	    else:
		gamelist.append('%s%s'%(opp, date))
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

def render_mailTo(user):
    users = getUserlist()
    email = []
    for u in users.keys():
	email.append(users[u]['email'])
    print "<a href='mailto:%s'>Email all playsers</a>" % ','.join(email)

def render_vote(user):
    try:
	expGames = getGamelist(exp=True)
	voteTime = time.strftime('%F %H:%M:%S')
	form = cgi.FieldStorage()
	for game in getGamelist():
	    game = game.strip()
	    if game not in expGames: continue
	    opp = form[game].value
	    opp = opp.strip()
	    ku = form['%s - ku'%game].value
	    ku = ku.strip()
	    if ku == '0' or opp == '0' or ku == '' or opp == '':
		continue
	    else:
		with open('/usr/share/rcc/.rawScores', 'a') as f:
		    f.write("%s -- %s: %s, %s\n"% (voteTime, game, ku,
			opp))
		team = False
		with open('/usr/share/rcc/.scores', 'r') as f:
		    lines = f.readlines()
		for line in lines:
		    lineNum = lines.index(line)
		    newScore = False
		    if line.startswith('[%s]' % game.split(' - ')[0]):
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
		with open('/usr/share/rcc/.scores', 'w') as f:
		    for line in lines:
			f.write("%s" % line)
		print "Scores collected: %s KU: %s, %s: %s<br/>"%(game,
			ku, game.split(' - ')[0].split(' ', 1)[1], opp)
    except KeyError:
	print "Click 'Opponent' to sort"
	template = Template(file('vote.html', 'r').read())
	print str(template.render(userScores=getUserGames(user,
	    null=True),gameInfo=getGamelist(gsplit=True),
	    expGames=getGamelist(exp=True, gameOnly=True)))
    except Exception, e:
	print '<pre>'
	print traceback.format_exc()
	print '</pre>'

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
    with open('/usr/share/rcc/.scores', 'r') as f:
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
#    tempVars['diff'] = abs(tempVars['kuActual'] - tempVars['oppActual'])
		players[player]['diff'] = \
			abs(players[player]['kuGuess'] \
			- players[player]['oppGuess'])
		players[player]['adjScore'] = 100 -  abs( \
			abs(tempVars['kuActual'] - players[player]['kuGuess']) \
			+ abs(tempVars['oppActual'] - players[player]['oppGuess']) \
			+ abs(tempVars['diff'] - players[player]['diff']))
	    tempVars['players'] = players

    template = Template(file('viewStandings.html', 'r').read())
    print str(template.render(**tempVars))

def render_prefs(user):
    form = cgi.FieldStorage()
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
		subprocess.check_call('htpasswd -b /home/thedav4/kurcc.com/.htpasswd %s %s' % ( changeUser, changePassword), shell=True)
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

	if cmd == 'scores':
	    with open('/usr/share/rcc/.scores') as f:
		for line in f:
		    print "<p>%s</p>" % line

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
		subprocess.check_call('htpasswd -b /home/thedav4/kurcc.com/.htpasswd %s %s' % ( changeUser, changePassword), shell=True)
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
	    with open('/usr/share/rcc/.scores', 'r') as f:
		lines = f.readlines()
	    for line in lines:
		lineNum = lines.index(line)
		newScore = False
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
	    with open('/usr/share/rcc/.scores', 'w') as f:
		for line in lines:
		    f.write("%s" % line)
	    print "Scores collected, thank you"
	if cmd == 'writeMOTD':
	    newMotd = form['motd'].value
	    with open('/usr/share/rcc/motd', 'w') as f:
		for line in newMotd.split('\n'):
		    f.write(line)
	template = Template(file('admin.html', 'r').read())
		

	print str(template.render(gamelist=getGamelist(gameOnly=True),
	    userlist=userlist, newusers=getUserlist(new=True),
	    motd=getMOTD()))

def render_userlist(user):
    template = Template(file('players.html', 'r').read())
    print str(template.render(players=getUserlist()))

def render_groupStats(user):
    pass

def render_stats(user):
    u = user
    print "<table class='sortable' width='100%' border=1>"
    print """
    <tr>
	<th>Username</th>
	<th>Games played</th>
	<th>Total games</th>
	<th>% of games played</th>
	<th>Overall score</th>
    </tr>"""
    for user in userlist:
	t = {}
	t['userGames'] = getUserGames(user)
	t['games'] = getGamelist(gameOnly=True)
	t['numGames'] = len(t['games'])
	t['numPlayed'] = len(t['userGames'])
	t['playPerc'] = "%0.2f" % (((0.00+t['numPlayed'])/t['numGames'])*100)
	t['overallScore'] = getOverallScore(user)
	for game in t['userGames']:
	    if game in t['games']:
		t['games'].pop(t['games'].index(game))
	template = Template(file('playerStats.html', 'r').read())
	print str(template.render(u=u, user=user, **t))
    print "</table>"

def render_(user):
    pass

def deliverContent(qstring, user):
    exec('render_%s(user)' % qstring)

def getUserGames(userToPoll, null=False):
    stats = {}
    team = None
    with open('/usr/share/rcc/.scores', 'r') as f:
	lines = f.readlines()
    for line in lines:
	lineNum = lines.index(line)
	newScore = False
	if line.startswith('['):
	    team = line.strip('[]\n')
	elif line.startswith(userToPoll) and team:
	    scores = line.split(':')[1]
	    ku = scores.split(',')[0]
	    opp = scores.split(',')[1]
	    stats[team] = [ku.strip(), opp.strip()]
	    continue
    if null and team:
	for team in getGamelist(gsplit=True).values():
	    if team not in stats.keys():
		stats[team] = [0, 0]
    return stats

def getOverallScore(u):
    games = getGamelist(gameOnly=True, over=True)
    kuActual=0
    oppActual=0
    overallScore = 0
    for game in games:
	with open('/usr/share/rcc/.actualScores.txt', 'r') as f:
	    for line in f.readlines():
		line = line.split(':')
		team = line[0]
		if team == game:
		    kuActual = int(line[1].split(',')[0])
		    oppActual = int(line[1].split(',')[1])
	with open('/usr/share/rcc/.scores', 'r') as f:
	    for line in f.readlines():
		if line.startswith('[%s]'%game):
		    team = True
		elif line.startswith('['):
		    team = False
		elif team == True:
		    nline = line.split(':')
		    if u == nline[0]:
			kuGuess = int(nline[1].split(',')[0])
			oppGuess = int(nline[1].split(',')[1])
		    #tempVars['diff'] = abs(tempVars['kuActual'] - tempVars['oppActual'])
#		players[player]['diff'] = \
	    #			abs(players[player]['kuGuess'] \
	    #		- players[player]['oppGuess'])
			playerDiff = abs(oppGuess - kuGuess)
			diff = abs(kuActual - oppActual)
#			abs(tempVars['kuActual'] - players[player]['kuGuess']) \
#			+ abs(tempVars['oppActual'] - players[player]['oppGuess']) \
#			+ abs(tempVars['diff'] - players[player]['diff']))
			overallScore += 100 - abs( \
				-abs(abs(kuActual-kuGuess) \
				+abs(oppActual-oppGuess) \
				+abs(diff-playerDiff)))
			break
    return overallScore
