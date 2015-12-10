import json
import sys
import time
import socket
import ssl
import os
import glob
import re
import threading
import format

reload(sys)

sys.setdefaultencoding('utf-8')

local = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

time_milli = lambda: int(round(time.time() * 1000))

class Bot():


    version = '0.0.1'

    buffer = ''

    start_time = 0

    config = {}

    commands = {}

    events = {}

    running = False

    nick = ''

    chans = []

    check_perms = []

    flood_check = {}


    def __init__(self):

        self.socket = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

        if not self.load():

            sys.exit('Failed to load; exiting.')


    def thread(self, func, params=()):

        thread = threading.Thread(target=func, args=params)

        thread.start()


    def die(self, message):

        print 'Killed (%s)' % message

        self.running = False


    def save(self):

        with open(os.path.join(local, 'config.json'), 'w') as fp:

            json.dump(self.config, fp, indent = 2)


    def load(self):

        self.start_time = time.time()

        print 'Initiating v%s:' % self.version

        print 'Loading settings...'

        try:

            with open(os.path.join(local, 'config.json'), 'r') as fp:

                self.config = json.load(fp)

        except:

            return False

        print 'Settings loaded.'

        print 'Loading modules...'

        try:

            self.events = {}

            self.commands = {}

            files = set(glob.glob(os.path.join('modules', '*.py')))

            for file in files:

                print 'file: ' + file

                code = compile(open(os.path.join(local, file), 'U').read(), file, 'exec')

                namespace = {
                    'bot': self
                }

                eval(code, namespace)

                commands = []

                events = []

                for obj in namespace.itervalues():

                    if hasattr(obj, '_command'):

                        for command in obj._command:

                            if command not in self.commands:

                                self.commands[command] = []

                            self.commands[command].append(obj)

                            commands.append(command)

                    if hasattr(obj, '_event'):

                        for event in obj._event:

                            if event not in self.events:

                                self.events[event] = []

                            self.events[event].append(obj)

                            events.append(event)

                events = ', '.join(events) if len(events) else 'None'

                commands = ', '.join(commands) if len(commands) else 'None'

                print 'Loaded %s (Events: %s) (Commands: %s)' % (file, events, commands)

        except Exception, e:

            print 'error: ' + str(e)

            return False

        print 'Modules loaded.'

        return True


    def connect(self):

        print 'CONNECT .........'
        print self.config['server']
        print self.config['port']

        try:
            self.socket.connect((self.config['server'], self.config['port']))
        except Exception, e:
            print 'wat: ' + str(e)

        print 'conn.......'

        self.raw('NICK %s' % self.config['nick'])
        self.raw('PASS %s' % self.config['pass'])

        wat = 'USER %s 8 * :%s' % (self.config['ident'],self.config['nick'])
        print wat
        #self.raw('USER %s 8 * :%s' % (self.config['ident'],self.config['nick']))
        self.raw(wat)

        self.loop()


    def raw(self, message):

        message += '\r\n'

        self.socket.send(message)


    def do(self, command, *args):

        self.raw(command + ' ' + ' '.join(args))


    def oper(self):

        if bot.config['oper_name'] and bot.config['oper_pass']:

            bot.do('OPER', bot.config['oper_name'], bot.config['oper_pass'])


    def say(self, to, message):

        if to not in self.flood_check:

            self.flood_check[to] = [time_milli(), 0]


        diff = time_milli() - self.flood_check[to][0]

        delay = self.config['flood_delay']

        limit = self.config['flood_limit']


        if diff < delay:

            self.flood_check[to][1] += 1

        else:

            self.flood_check[to][1] -= min(int(diff / delay), self.flood_check[to][1])


        self.flood_check[to][0] = time_milli()


        if self.flood_check[to][1] >= limit:

            if self.flood_check[to][1] == limit and self.config['log']:

                self.say(self.config['log'], 'Flood triggered in %s.' % to)

            print 'Flood triggered in %s.' % to

        else:

            self.raw('PRIVMSG %s :%s' % (to, message))


    def log(self, message):

        if self.config['log']:

            bot.say(self.config['log'], message)


    def join(self, chans):

        for chan in chans:

            print 'JOIN %s' % chan

            self.raw('JOIN %s' % chan)


    def part(self, chans):

        for chan in chans:

            self.raw('PART %s' % chan)


    def loop(self):

        self.running = True

        while self.running:

            try:

                self.buffer = self.buffer + self.socket.recv(2048)

            except:

                sys.exit('ERROR: Failed to recv.')

            lines = str.split(self.buffer, '\r\n')

            self.buffer = lines.pop()

            for line in lines:

                # print line
                print line

                regex = re.compile(r'^(?::([^@!\ ]*)(?:(?:\!([^@]*))?@([^\ ]*))?\ )?([^\ ]+)\ ?((?:[^:\ ]*){0,14})(?:\ :?(.*))?$')

                nick, ident, host, type, destination, message = re.findall(regex, line)[0]

                params = message.split(' ')

                # do events

                if type in self.events:

                    for func in self.events[type]:

                        self.thread(func, ((nick, ident, host), destination, params))

                # do commands

                print 'params[0] : ' + params[0]
                print 'self.config[\'prefix\'] : '+ self.config['prefix']
                try:
                    if params[0].startswith(self.config['prefix']):

                        command = params[0][1:]

                        params.pop(0)

                        if command in self.commands:

                            if self.config['log'] and destination != self.config['log']:

                                self.say(self.config['log'], '%s %s called by %s in %s (%s)' % (
                                    format.color('Command:', format.GREEN),
                                    command,
                                    nick,
                                    destination,
                                    ', '.join(params)
                                    ))

                            if destination == self.nick:

                                destination = nick

                            for func in self.commands[command]:

                                # admin perm overrides all

                                if host in self.config['perms']['admin']:

                                    self.thread(func, ((nick, ident, host), destination, params))

                                    continue

                                # perms override flags

                                elif hasattr(func, '_perm'):

                                    perm = getattr(func, '_perm')

                                    if perm not in self.config['perms']:

                                        continue

                                    if host not in self.config['perms'][perm]:

                                        continue

                                # check required flags

                                elif hasattr(func, '_flags'):

                                    self.check_perms.append({
                                        'nick': nick,
                                        'func': func,
                                        'perm': getattr(func, '_flags'),
                                        'chan': destination,
                                        'args': ((nick, ident, host), destination, params)
                                    })

                                    self.do('WHO', destination)

                                    continue

                                self.thread(func, ((nick, ident, host), destination, params))
                except UnicodeDecodeError:
                    print 'DECODE ERROR'


bot = Bot()

bot.connect()
