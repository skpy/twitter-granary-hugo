import datetime
from dateutil import tz
import json
import sys
import time
import os

from granary import microformats2
from granary import twitter

reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == '__main__':
    # set up our timezone objects, so we can set local times on all posts
    utc = tz.gettz('UTC')
    est = tz.gettz('America/New_York')

    # load tweet JSON from command line argument
    posts = json.loads(open(sys.argv[1], 'r').read())

    os.system('mkdir -p notes')

    last_date = ''
    counter = 0
    for post in posts:
        decoded = twitter.Twitter('token', 'secret', 'smerrill').tweet_to_activity(post)
        obj = twitter.Twitter('token', 'secret', 'smerrill').tweet_to_object(post)
        # first we need to deal with legacy tweets in the export, because they
        # all have a published time of midnight UTC on the day of publication.
        # Set them to my timezone while I'm at it.
        date = datetime.datetime.strptime(decoded['published'], "%Y-%m-%d %H:%M:%S +0000").replace(tzinfo=utc).astimezone(est)
        # we have the date, which is enough to build the directory path
        path = "notes/%s" % date.strftime('%Y/%m/%d')
        if not os.path.isdir(path):
            os.makedirs(path)
            index = "%s/_index.md" % path
            open(index,'w').close()
        if last_date == date:
            # this tweet has the same timestamp as the last one.
            # we'll just increment by one minute. I don't recall ever
            # having tweeted more than 60 times in a day.
            counter += 1
            date = date + datetime.timedelta(minutes=counter)
        else:
            counter = 0
            last_date = date
        # now we have a unique date and time, which we can use to
        # create the output file
        filename = "notes/%s/%s.md" % (date.strftime('%Y/%m/%d'), date.strftime('%H%M%S'))
        file = open(filename, 'w')
        file.write('---\n')
        file.write('author: skippy\n')
        file.write("date: %s\n" % date.strftime('%Y-%m-%d %H:%M:%S'))

        # now we figure out what kind of Tweet this is:
        # new post, reply to someone, or retweet.
        # i don't "like" anything, so i don't need to worry about
        # that activity here.
        if decoded['verb'] == 'share':
            # we'll deal with retweets first.
            file.write("retweet_url: %s\n" % decoded['object']['url'])
            file.write("retweet_user: %s\n" % decoded['object']['author']['username'])
        if decoded['verb'] == 'post':
            # this is either a new post, or a reply
            if 'inReplyTo' in decoded['object']:
                # okay, this is a rewteet.
                # but sometimes the user ID is invalid.
                if 'tags' in decoded['object'] and decoded['object']['tags'][0]['url']:
                    reply_user = "'@%s'" % decoded['object']['tags'][0]['url'].replace('https://twitter.com/', '')
                else:
                    reply_user = 'a former Twitter user'
                file.write("reply_to_user: %s\n" % reply_user)
                file.write("reply_to_url: %s\n" % decoded['object']['inReplyTo'][0]['url'])

        file.write("tweet_url: %s\n" % decoded['url'])
        file.write('---\n')
        # we use the render_content() method here to ensure that we get
        # untruncated links in the output.
        file.write('%s\n' % microformats2.render_content(obj, False))
        file.write("\n")
        file.close()

        #with open('mf2/%s.json' % mf2['properties']['published'][0], 'wb') as mf2_file:
        #  mf2_file.write(mf2_json)

