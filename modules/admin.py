# admin commands

import hook
import os
import sys
import time
import threading


@hook.command('oper', perm='admin')
def oper(prefix, destination, params):

    bot.oper()


@hook.command('flood', perm='admin')
def flood(prefix, destination, params):

    for i in range(int(params[1])):

        bot.say(params[0], ' '.join(params[2:]))


@hook.command('say', perm='admin')
def say(prefix, destination, params):

    bot.say(params[0], ' '.join(params[1:]))


@hook.command('restart', perm='admin')
def restart(prefix, destination, params):

    bot.do('QUIT', ' '.join(params))

    os.execl(sys.executable, sys.executable, * sys.argv)


@hook.command('reload', perm='admin')
def reload(prefix, destination, params):

    bot.load()


@hook.command('nick', perm='admin')
def nick(prefix, destination, params):

    bot.do('NICK', params[0])


@hook.command('quit', perm='admin')
def quit(prefix, destination, params):

    bot.log('Exiting... (requested by %s)' % prefix[0])

    bot.do('QUIT', ' '.join(params))

    bot.die(prefix[0])


@hook.command('raw', perm='admin')
def raw(prefix, destination, params):

    bot.raw(' '.join(params))


@hook.command('join', perm='admin')
def join_chan(prefix, destination, params):

    bot.join(params)


@hook.command('part', perm='admin')
def part_chan(prefix, destination, params):

    if len(params):

        bot.part(params)

    else:

        bot.part([destination])


@hook.command('sys', perm='admin')
def sysinfo(prefix, destination, params):

    seconds = time.time() - bot.start_time

    times = []

    days = seconds // 86400
    hours = seconds // 3600 % 24
    minutes = seconds // 60 % 60
    seconds = seconds % 60

    if days: times.append('%s days' % int(days))
    if hours: times.append('%s hours' % int(hours))
    if minutes: times.append('%s minutes' % int(minutes))
    if seconds: times.append('%s seconds' % int(seconds))

    bot.say(destination, 'Version: %s Uptime: %s Threads: %s' % (
        bot.version,
        ', '.join(times),
        threading.activeCount()
        ))
