#!/usr/bin/python

import os, sys, time, cgi, cgitb, subprocess, traceback, crypt
import psycopg2
from datetime import tzinfo, timedelta, datetime
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
    over -- If set to true, only adds games which 2 hours have elapsed
	    since their start
    gameOnly -- Only return the games, no times or dates
    gsplit -- Split the opposing team and time into a dictionary
    """

    gamelist = []
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    if exp:
	cur.execute("SELECT * FROM games WHERE time + interval '5m' <= "
		"'now';")
    elif over:
	cur.execute("SELECT * FROM games WHERE time + interval '2h' <= "
		"'now';")
    else:
	cur.execute("SELECT * FROM games;")
    for game in cur.fetchall():
	if gameOnly:
	    gamelist.append({"team": game[0]})
	else:
	    gamelist.append({"team": game[0], 
		"time": game[1].astimezone(CST()).strftime("%Y-%m-%d %H:%M:%S")})
    cur.close()
    conn.close()
    return gamelist

def getUserlist(new=False):
    # Find playings requesting access
    userSource = "userlist"
    if new:
	userSource = "userrequests"
    users = {}
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    cur.execute("SELECT * FROM %s;"%(userSource))
    for user in cur.fetchall():
	users[user[0]] = {
		'username' : user[0],
		'htpasswd' : user[1],
		'name' : user[2],
		'email' : user[3],
		'address' : user[4]
		}
    cur.close()
    conn.close()
    return users

def getMOTD():
    with open('/usr/share/rcc/motd', 'r') as f:
	return f.read()

def render_mailTo(user):
    users = getUserlist()
    email = []
    for u in users.keys():
	email.append(users[u]['email'])
    print "<a href='mailto:%s'>Email all playsers</a>" % ','.join(email)

class CST(tzinfo):
    def utcoffset(self, dt):
	return timedelta(hours=-6)
    def dst(self, dt):
	return timedelta(0)
    def tzname(self, dt):
	return "America/Chicago"

class PST(tzinfo):
    def utcoffset(self, dt):
	return timedelta(hours=-8)
    def dst(self, dt):
	return timedelta(0)
    def tzname(self, dt):
	return "America/Los_Angeles"

#def render_testvote(user):
#    try:
#	expGames = getGamelist(exp=True)
#	voteTime = datetime.now(CST()).isoformat()
#	form = cgi.FieldStorage()
#	for game in getGamelist():
#	    if game["time"] in [g['time'] for g in expGames]: 
#		continue
#	    team = game["team"].strip()
#	    gametime = game["time"].strip()
#	    opp = form[gametime].value
#	    opp = opp.strip()
#	    ku = form['%s - ku'%gametime].value
#	    ku = ku.strip()
#	    if ku == '0' or opp == '0' or ku == '' or opp == '':
#		continue
#	    else:
#		conn = psycopg2.connect("dbname=rcc user=tdavis "
#			"password=madman12 host=127.0.0.1")
#		cur = conn.cursor()
#		cur.execute("SELECT * FROM scores WHERE username=%s "
#			"AND gametime=%s;", (user, gametime))
#		if cur.fetchone():
#		    cur.execute("UPDATE scores SET opp=%s, ku=%s, "
#			    "time=%s WHERE username=%s AND "
#			    "gametime=%s;", (opp, ku, voteTime, user, gametime))
#		else:
#		    cur.execute("INSERT INTO scores (username, team, opp, "
#			    "ku, time, gametime) VALUES (%s, %s, %s, %s, %s, "
#			    "%s);", (user, team, opp, ku, voteTime, gametime))
#		cur.close()
#		conn.commit()
#		conn.close()
#		print "Scores collected: KU: %s, %s: %s<br/>"%(ku, game["team"], opp)
#    except KeyError:
#	print "Click 'Opponent' to sort"
#	ended = {}
#	template = Template(file('vote.html', 'r').read())
#	vars = {"userScores": getUserGames(user, null=True), 
#		"gameInfo": getGamelist(gsplit=True), 
#		"expGames": getGamelist(exp=True)
#		#[g["team"] for g in getGamelist(exp=True, gameOnly=True)]
#		}
#	for game in vars["gameInfo"]:
#	    if game in vars["expGames"]:
#		del(vars["gameInfo"][game])
#	print str(template.render(**vars))
#    except Exception, e:
#	print '<pre>'
#	print traceback.format_exc()
#	print '</pre>'

def render_vote(user):
    try:
	expGames = getGamelist(exp=True)
	voteTime = datetime.now(CST()).isoformat()
	form = cgi.FieldStorage()
	for game in getGamelist():
	    if game["time"] in [g['time'] for g in expGames]: 
		continue
	    team = game["team"].strip()
	    gametime = game["time"].strip()
	    opp = form[gametime].value
	    opp = opp.strip()
	    ku = form['%s - ku'%gametime].value
	    ku = ku.strip()
	    if ku == '0' or opp == '0' or ku == '' or opp == '':
		continue
	    else:
		conn = psycopg2.connect("dbname=rcc user=tdavis "
			"password=madman12 host=127.0.0.1")
		cur = conn.cursor()
		cur.execute("SELECT * FROM scores WHERE username=%s "
			"AND gametime=%s;", (user, gametime))
		if cur.fetchone():
		    cur.execute("UPDATE scores SET opp=%s, ku=%s, "
			    "time=%s WHERE username=%s AND "
			    "gametime=%s;", (opp, ku, voteTime, user, gametime))
		else:
		    cur.execute("INSERT INTO scores (username, team, opp, "
			    "ku, time, gametime) VALUES (%s, %s, %s, %s, %s, "
			    "%s);", (user, team, opp, ku, voteTime, gametime))
		cur.close()
		conn.commit()
		conn.close()
		print "Scores collected: KU: %s, %s: %s<br/>"%(ku, game["team"], opp)
    except KeyError:
	print "Click 'Opponent' to sort"
	ended = {}
	template = Template(file('vote.html', 'r').read())
	vars = {"userScores": getUserGames(user, null=True), 
		"gameInfo": getGamelist(), 
		"expGames": getGamelist(exp=True)
		#[g["team"] for g in getGamelist(exp=True, gameOnly=True)]
		}
	for game in vars["gameInfo"][:]:
	    if game in vars["expGames"]:
		del(vars["gameInfo"][vars['gameInfo'].index(game)])
	print str(template.render(**vars))
    except Exception, e:
	print '<pre>'
	print traceback.format_exc()
	print '</pre>'

def render_standings(user):
    template = Template(file('standings.html', 'r').read())
    print str(template.render(gamelist=getGamelist(over=True)))

def render_viewStandings(user):
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    games = getGamelist(over=True)
    form = cgi.FieldStorage()
    game = form['game'].value
    tempVars = {'user': user, 'game': game}
    players = {}

    cur.execute("SELECT * FROM gamescores WHERE time='%s';"%(game+" -06"))
    score = cur.fetchone()
    tempVars['kuActual'] = score[1]
    tempVars['oppActual'] = score[2]
    tempVars['diff'] = tempVars['kuActual'] - tempVars['oppActual']

    for player in getUserlist():
	players[player] = {}
	cur.execute("SELECT * FROM scores WHERE username=%s AND "
	    "gametime=%s;", (player, game))
	score = cur.fetchone()
	if not score:
	    continue
	try:
	    players[player]['oppGuess'] = score[2]
	    players[player]['kuGuess'] = score[3]
	    players[player]['diff'] = players[player]['kuGuess'] \
		    - players[player]['oppGuess']
	    players[player]['adjScore'] = 100 -  abs( \
		    abs(tempVars['kuActual'] - players[player]['kuGuess']) \
		    + abs(tempVars['oppActual'] - players[player]['oppGuess']) \
		    + abs(tempVars['diff'] - players[player]['diff']))
	except Exception, e:
	    pass
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
		subprocess.check_call('htpasswd -b '
			'/home/tdavis/site/rcc/.htpasswd %s %s' % ( changeUser,
			    changePassword), shell=True)
		print "Password Changed"
	    except:
		print "<pre>%s</pre>"%(cgi.escape(traceback.format_exc()))
	else:
	    print "Passwords did not match"

def render_admin(user):
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    if user in adminList:
	form = cgi.FieldStorage()

	try:
	    cmd = form['cmd'].value
	except Exception, e:
	    cmd = 'MAIN'

	if cmd == 'denyUser':
	    users = form['newuser']
	    try:
		if len(users)>1:
		    pass
		else:
		    users = [form['newuser']]
	    except Exception, e:
		users = [form['newuser']]
	    for newuser in users:
		cur.execute("DELETE FROM userrequests WHERE username='%s'"%
			newuser.value)

	if cmd == 'registerUser':
	    users = form['newuser']
	    try:
		if len(users)>1:
		    pass
		else:
		    users = [form['newuser']]
	    except Exception, e:
		users = [form['newuser']]
	    for newuser in users:
		cur.execute("SELECT * FROM userrequests WHERE username=%s;",
			(newuser.value, ))
		user = cur.fetchone()
		if user:
		    cur.execute("INSERT INTO userlist (username, htpasswd, name, "
			    "email, address) VALUES (%s, %s, %s, %s, %s);",
			    (user[0], user[1], user[2], user[3], user[4]))
		    cur.execute("DELETE FROM userrequests WHERE username='%s';"% (user[0]))
		    subprocess.check_call('htpasswd -b '
			    '/home/tdavis/site/rcc/.htpasswd %s %s' % 
			    ( user[0], user[1]), shell=True)
		    with open("/home/tdavis/requests", "a") as f:
			f.write("%s\n"%user[3])

	if cmd == 'changePassword':
	    changeUser = form['cuser'].value
	    changePassword = form['changePassword'].value
	    changePassword = changePassword.replace('"', '\\"')
	    changePassword = changePassword.replace(';', '\\;')
	    changePassword = changePassword.replace('|', '\\|')
	    changePassword = changePassword.replace(' ','\\ ')

	    try:
		subprocess.check_call('htpasswd -b '
			'/home/tdavis/site/rcc/.htpasswd %s %s' % ( changeUser,
			    changePassword), shell=True)
		print "Password Changed"
	    except:
		print "<pre>%s</pre>"%(cgi.escape(traceback.format_exc()))

	if cmd == 'enterScores':
	    ku = form['ku'].value
	    opp = form['opp'].value
	    game = form['game'].value
	    gametime = str(game.split(',')[0]+" -0600")
	    game = game.split(',')[1]
	    cur.execute("SELECT * FROM gamescores;")
	    games = cur.fetchall()
	    if gametime in [g[3] for g in games]:
		cur.execute("UPDATE gamescores SET team=%s, opp=%s, ku=%s, "
			"WHERE time=%s", (game, opp, ku, gametime))
	    else:
		cur.execute("INSERT INTO gamescores (team, opp, ku, time) "
			"VALUES (%s, %s, %s, %s);", (game, opp, ku, gametime))
	    print "Scores collected, thank you"
	    
	if cmd == 'changeScores':
	    pass
	    changeUser = form['user'].value
	    ku = form['ku'].value
	    opp = form['opp'].value
	    game = form['game'].value
	    gametime = game.split(',')[0]
	    game = game.split(',')[1]

	    conn = psycopg2.connect("dbname=rcc user=tdavis "
		    "password=madman12 host=127.0.0.1")
	    cur = conn.cursor()
	    cur.execute("SELECT * FROM scores WHERE username=%s "
		    "AND gametime=%s;", (changeUser, gametime))
	    if cur.fetchone():
		cur.execute("UPDATE scores SET opp=%s, ku=%s "
			"WHERE gametime=%s AND username=%s;", (opp, ku, 
			    gametime, changeUser))
	    else:
		cur.execute("INSERT INTO scores (username, team, opp, ku, "
			"gametime) VALUES (%s, %s, %s, %s, %s);", (changeUser, 
			    game, opp, ku, gametime))
	    cur.close()
	    conn.commit()
	    conn.close()
	    print "Scores collected, thank you"
	if cmd == 'writeMOTD':
	    newMotd = form['motd'].value
	    with open('/usr/share/rcc/motd', 'w') as f:
		for line in newMotd.split('\n'):
		    f.write(line)
	template = Template(file('admin.html', 'r').read())
		

	print str(template.render(gamelist=getGamelist(),
	    userlist=getUserlist(), newusers=getUserlist(new=True),
	    motd=getMOTD()))
    cur.close()
    conn.commit()
    conn.close()

def render_delete(user):
    form = cgi.FieldStorage()
    user = form['user'].value

    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    cur.execute("SELECT * FROM userlist WHERE username='%s';"%user)
    if cur.fetchone():
	cur.execute("DELETE FROM userlist WHERE username='%s';"%user)
	subprocess.check_call('htpasswd -D /home/tdavis/site/rcc/.htpasswd %s' % 
		( user), shell=True)
	print "Successfully deleted %s" % user
    else:
	pass
	
    cur.close()
    conn.commit()
    conn.close()



def render_userlist(user):
    if user not in adminList:
	pass
    else:
	template = Template(file('players.html', 'r').read())
	print str(template.render(players=getUserlist()))

def render_stats(user):
    u = user
    print "<table class='sortable' width='100%' border=1>"
    print """
    <tr>
	<th>Username</th>
	<th>Games played</th>
	<th>Total games</th>
	<th>% of games played</th>
	<th>Season average</th>
    </tr>"""
    for user in getUserlist():
	t = {}
	t['userGames'] = getUserGames(user, over=True)
	t['games'] = getGamelist(gameOnly=True, over=True)
	t['numGames'] = len(t['games'])
	t['numPlayed'] = len(t['userGames'])
	if not t['numGames']: continue
	t['playPerc'] = "%0.2f" % (((0.00+t['numPlayed'])/t['numGames'])*100)
	t['overallScore'] = "%0.1f" % getOverallScore(user)
	for game in t['userGames']:
	    if game in t['games']:
		t['games'].pop(t['games'].index(game))
	template = Template(file('playerStats.html', 'r').read())
	print str(template.render(u=u, user=user, **t))
    print "</table>"

def render_(user):
    pass
def render_None(user):
    pass

def deliverContent(qstring, user):
    exec('render_%s(user)' % qstring)

def getPlayerRank(user, score):
    pass

def getUserGames(userToPoll, null=False, over=False):
    stats = {}
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    if over:
	cur.execute("SELECT * FROM games WHERE time + interval '2h'<='now';")
	teams = cur.fetchall()
	for gametime in [t[1].astimezone(CST()).strftime("%Y-%m-%d %H:%M:%S") for t in teams]:
	    cur.execute("SELECT * FROM scores WHERE username=%s AND "
		"gametime=%s;", (userToPoll, gametime))
	    game = cur.fetchone()
	    if not game: continue
	    try:
		opp = game[2]
		ku = game[3]
		stats[gametime] = [ku, opp]
	    except:
		pass
    else:
	cur.execute("SELECT * FROM games;")
	teams = cur.fetchall()
	for gametime in [t[1].astimezone(CST()).strftime("%Y-%m-%d %H:%M:%S") for t in teams]:
	    cur.execute("SELECT * FROM scores WHERE username=%s AND "
		"gametime=%s;", (userToPoll, gametime))
	    game = cur.fetchone()
	    try:
		opp = game[2]
		ku = game[3]
		stats[gametime] = [ku, opp]
	    except:
		pass
    if null:
	cur.execute("SELECT * FROM games;")
	teams = cur.fetchall()
	for gametime in [t[1].astimezone(CST()).strftime("%Y-%m-%d %H:%M:%S") for t in teams]:
	    #for team in getGamelist(gsplit=True).values():
	    if gametime not in stats.keys():
		stats[gametime] = [0, 0]

    cur.close()
    conn.close()
    return stats

def getOverallScore(u):
    conn = psycopg2.connect("dbname=rcc user=tdavis password=madman12 "
	    "host=127.0.0.1")
    cur = conn.cursor()
    games = getGamelist(over=True)
    kuActual=0
    oppActual=0
    overallScore = 0
    for game in games:
	cur.execute("SELECT * FROM gamescores WHERE time='%s';"%
		(str(game['time']+" -06")))
	curgame = cur.fetchone()
	if not curgame: 
	    continue
	kuActual = curgame[1]
	oppActual = curgame[2]

	cur.execute("SELECT * FROM scores WHERE username=%s AND gametime=%s", 
		(u, game['time']))
	curuser = cur.fetchone()
	if not curuser: 
	    continue
	kuGuess = curuser[3]
	oppGuess = curuser[2]
	playerDiff = kuGuess - oppGuess
	diff = kuActual - oppActual
	overallScore += (100.0 - abs( \
		-abs(abs(kuActual-kuGuess) \
		+abs(oppActual-oppGuess) \
		+abs(diff-playerDiff))))
    if overallScore == 0:
	return 0.0

    return overallScore / len(getUserGames(u, over=True))
