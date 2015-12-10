# Basic events required to function

import hook
import time


@hook.event('PRIVMSG')
def pm(prefix, destination, params):

    if destination == bot.nick and bot.config['log']:

        bot.say(bot.config['log'], '%s: %s' % (prefix[0], ' '.join(params)))


@hook.event('PING')
def ping(prefix, destination, params):

    bot.do('PONG', params[0])


@hook.event('NICK')
def nick_changed(prefix, destination, params):

    if prefix[0] == bot.nick:

        bot.nick = destination


@hook.event('001')
def logged_in(prefix, destination, params):

    bot.nick = destination

    time.sleep(2)

    bot.do('MODE', bot.config['nick'], '+B')

    bot.join(bot.config['chans'])


@hook.event('INVITE')
def invited(prefix, destination, params):
    
    pass
    #bot.join(params)


@hook.event('JOIN')
def bot_joined(prefix, destination, params):

    if prefix[0] == bot.nick:

        bot.chans.append(params[0])

        if params[0] not in bot.config['chans']:

            bot.config['chans'].append(params[0])

            bot.save()


@hook.event('PART')
def bot_parted(prefix, destination, params):

    if prefix[0] == bot.nick:

        bot.chans.remove(destination)

        if destination in bot.config['chans']:

            bot.config['chans'].remove(destination)

            bot.save()


@hook.event('KICK')
def bot_kicked(prefix, destination, params):

    if params[0] == bot.nick:

        bot.chans.remove(destination)

        if destination in bot.config['chans']:

            bot.config['chans'].remove(destination)

            bot.save()


# check user status for flag requirements

@hook.event('352')
def check_ops(prefix, destination, params):

    # [channel, ident, host, server, nick, status (* staff, !@%+, G away), hopcount, realname]

    if len(params) < 8: return

    nick = params[4]
    chan = params[0]
    stat = params[5]

    for thing in bot.check_perms:

        if thing['nick'] == nick and thing['chan'] == chan:

            for perm in thing['perm']:

                if perm in stat:

                    bot.thread(thing['func'], thing['args'])

                    bot.check_perms.remove(thing)

                    return

            bot.check_perms.remove(thing)
