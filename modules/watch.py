import praw
import time
import hook
import format
import re
from urlparse import urlparse


r = praw.Reddit(user_agent = 'IRC SubWatch by /u/Dissimulate ver %s' % bot.version)


def print_help(chan):

    bot.say(chan, 'Use $add/$del <sub> key|words|here to add/del a sub with optional trigger words.')
    bot.say(chan, 'Use $start/$stop to unpause or pause SubWatch on the channel.')
    bot.say(chan, 'Use $list to view the subs being watched on the channel.')


try:

    print 'Attempting to log in to reddit...'

    r.login(bot.config['reddit_user'], bot.config['reddit_pass'], disable_warning=True)

    print 'Logged in to reddit.'

except:

    sys.exit('Error: could not log in to reddit')


multi_reddits = []

sub_list = []

multi_size = 5


def get_submissions(multi):

    global multi_reddits

    start = bot.start_time

    while multi['list'] and start == bot.start_time:

        if multi['updated']:

            multi['sub'] = r.get_subreddit('+'.join(multi['list']))


        new_threads = []

        try:

            for thread in multi['sub'].get_new(limit = len(multi['list']) * 5):

                if thread.created_utc > multi['time']:

                    new_threads.append(thread)

            multi['time'] = time.time()

        except:

            print 'Failed to fetch new posts. %s' % time.strftime("%H:%M:%S")


        for thread in reversed(new_threads):

            sub = thread.subreddit.display_name

            prefix = 'Self post:' if thread.is_self else 'Link post:'

            url = thread.url if 'imgur' in urlparse(thread.url).netloc else urlparse(thread.url).netloc

            message = '%s: <%s> %s ( %s ) [ %s ] %s' % (
                format.bold('/r/'+sub),
                thread.author,
                thread.title,
                thread.short_link,
                'self.'+sub if thread.is_self else url,
                format.color(' NSFW', format.RED) if thread.over_18 else ''
            )

            '''
            message = '%s "%s" posted in /r/%s by %s. (%s)%s' % (
                format.color(prefix, format.GREEN),
                thread.title,
                sub,
                thread.author,
                thread.short_link,
                format.color(' NSFW', format.RED) if thread.over_18 else ''
            )
            '''

            for chan in bot.config['watch'][sub.lower()]:

                if chan in bot.config['stopped']: continue

                if len(bot.config['watch'][sub.lower()][chan]):

                    words = bot.config['watch'][sub.lower()][chan]

                    regex = re.compile(r'\b(%s)\b' % '|'.join(words), re.I)

                    if re.search(regex, thread.title):

                        def repl(match):

                            return format.bold(match.group(0))

                        new_title = re.sub(regex, repl, thread.title)

                        bot.say(chan, message.replace(thread.title, new_title))

                else:

                    bot.say(chan, message)

        time.sleep(30)


def add_multi():

    global sub_list

    if not sub_list:

        return

    multi = {
        'sub': r.get_subreddit('+'.join(sub_list)),
        'list': sub_list[:],
        'updated': False,
        'time': time.time()
    }

    multi_reddits.append(multi)

    sub_list = []


def setup():

    global sub_list

    global multi_reddits

    sub_list = []

    multi_reddits = []


    if 'watch' not in bot.config:

        bot.config['watch'] = {}

        bot.save()

    if 'stopped' not in bot.config:

        bot.config['stopped'] = []

        bot.save()


    if not bot.config['watch']: return


    for sub, chans in bot.config['watch'].iteritems():

        sub_list.append(sub)

        if len(sub_list) >= multi_size:

            add_multi()


    add_multi()


    for multi in multi_reddits:

        bot.thread(get_submissions, (multi,))


@hook.command('add', flags='%@')
def add_sub(prefix, chan, params):

    global multi_reddits

    try:

        sub = params[0].lower()

        words = params[1].split('|') if len(params) > 1 else []

    except:

        print_help(chan)

        return

    # check if sub is private or doesn't exist

    try:

        public = r.get_subreddit(sub).subreddit_type == 'public'

    except Exception as e:

        if isinstance(e, praw.errors.InvalidSubreddit):

            bot.say(chan, 'This subreddit doesn\'t appear to exist!')

            return

        if isinstance(e, praw.errors.Forbidden):

            bot.say(chan, 'The sub is not accessible, add /u/SnoonetSubWatch as an approved submitter first.')

            return

        bot.say(chan, 'The subreddit was not able to be added.')

        return


    # check if the channel name is given permission in /wiki/subwatch

    if not public:

        try:

            wiki = r.get_wiki_page(sub, 'subwatch').content_md

        except:

            bot.say(chan, 'Please add "%s" to /wiki/subwatch to grant access. Separate channels with a comma.' % chan)

            return

        chans = [x.strip() for x in wiki.split(',')]

        if chan not in chans:

            bot.say(chan, 'Please add "%s" to /wiki/subwatch to grant access. Separate channels with a comma.' % chan)

            return

    # add the sub to the channel

    if sub not in bot.config['watch']:

        bot.config['watch'][sub] = {}

        bot.config['watch'][sub][chan] = []

        for word in words:

            bot.config['watch'][sub][chan].append(word)

        added = False

        for multi in multi_reddits:

            if len(multi['list']) < multi_size:

                multi['list'].append(sub)

                added = multi['updated'] = True

                break

        if not added:

            multi = {
                'sub': r.get_subreddit(sub),
                'list': [sub],
                'updated': False,
                'time': time.time()
            }

            multi_reddits.append(multi)

            bot.thread(get_submissions, (multi,))

        bot.say(chan, '/r/%s successfully added to %s.' % (sub, chan))

        bot.save()

    else:

        if chan in bot.config['watch'][sub]:

            updated = False

            for word in words:

                if word not in bot.config['watch'][sub][chan]:

                    bot.config['watch'][sub][chan].append(word)

                    updated = True

            if updated:

                bot.say(chan, 'Keywords for /r/%s have been updated.' % sub)

                bot.save()

            else:

                bot.say(chan, '/r/%s has already been added to %s.' % (sub, chan))

            return

        else:

            bot.config['watch'][sub][chan] = []

            for word in words:

                bot.config['watch'][sub][chan].append(word)

            bot.say(chan, '/r/%s successfully added to %s.' % (sub, chan))

            bot.save()

    if not len(multi_reddits):

        setup()


@hook.command('del', flags='%@')
def del_sub(prefix, chan, params):

    global multi_reddits

    try:

        sub = params[0].lower()

        words = params[1].split('|') if len(params) > 1 else []

    except:

        print_help(chan)

        return

    if sub not in bot.config['watch'] or chan not in bot.config['watch'][sub]:

        bot.say(chan, '/r/%s has not been added to %s.' % (sub, chan))

        return


    if words:

        updated = False

        for word in words:

            if word in bot.config['watch'][sub][chan]:

                bot.config['watch'][sub][chan].remove(word)

                updated = True

        if updated:

            bot.say(chan, 'Keywords for /r/%s have been updated.' % sub)

            bot.save()

        return


    del bot.config['watch'][sub][chan]


    if not bot.config['watch'][sub]:

        del bot.config['watch'][sub]

        for multi in multi_reddits:

            if sub not in multi['list']: continue

            multi['list'].remove(sub)

            multi['updated'] = True

            if not multi['list']:

                multi_reddits.remove(multi)


    bot.say(chan, '/r/%s successfully deleted from %s.' % (sub, chan))

    bot.save()


@hook.command('list')
def list_sub(prefix, chan, params):

    subs = []

    for sub in bot.config['watch']:

        if chan in bot.config['watch'][sub]:

            if bot.config['watch'][sub][chan]:

                sub += ' (%s)' % ', '.join(bot.config['watch'][sub][chan])

            subs.append(sub)

    subs = ', '.join(subs) if len(subs) else 'None'

    bot.say(chan, 'Watched subs: %s' % subs)


@hook.command('stop', flags='%@')
def stop(prefix, chan, params):

    if chan not in bot.config['stopped']:

        bot.config['stopped'].append(chan)

        bot.say(chan, 'SubWatch has been paused in %s.' % chan)

        bot.save()


@hook.command('start', flags='%@')
def start(prefix, chan, params):

    if chan in bot.config['stopped']:

        bot.config['stopped'].remove(chan)

        bot.say(chan, 'SubWatch has been unpaused in %s.' % chan)

        bot.save()


@hook.command('help')
def showhelp(prefix, chan, params):

    print_help(chan)


setup()
