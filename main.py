import praw
import praw.exceptions
import config
import time
import re
import helpers
from sys import stdout
from frying import fry_url


def main():
    # list of subreddits to be continuously tracked
    subreddits = ['comedycemetery', 'deepfriedmemes', 'me_irl',
                  'meirl', 'memes', 'dankmemes', 'nukedmemes',
                  'whothefuckup', 'ComedyNecrophilia']

    
    # login to reddit and enter main loop
    reddit = login()
    sub = reddit.subreddit('+'.join(subreddits))
    while True:
        # check and fry username mentions
        check_mentions(reddit)
        
        # get comments from subreddits
        comments = list(sub.comments())

        # check for frying requests
        for comment in comments:
            check(comment)

def check_mentions(reddit):
    mentions = list(reddit.inbox.mentions())
    for comment in mentions:
        # verfify that the bot has not already replied to this comment
        try:
            comment.refresh()  # fetches comment's replies
            comment.replies.replace_more(limit=0)
        except praw.exceptions.ClientException as e:
            print(str(e))
            return
        check(comment)

# check comment for frying request
def check(comment):
    # Ignore too long comments
    if len(comment.body) > 50:
        # print("Comment too long, skipping.")
        return

    # remove special characters and change to lower case
    text = helpers.remove_specials(comment.body)

    # determine type of request
    if 'morefrying' in text:
        message = "Post needs more frying!"
        n = 1
    elif 'morenuking' in text:
        message = "Post needs more nuking!"
        n = 5
    else:
        # print("No frying requested.")
        return

    # verfify that the bot has not already replied to this comment
    try:
        comment.refresh()  # fetches comment's replies
        comment.replies.replace_more(limit=0)
    except praw.exceptions.ClientException as e:
        print(str(e))
        return
    for reply in comment.replies:
        if reply.author.name == 'DeepFryBot':
            print("Frying request already fulfilled.")
            return

    print(message)
    # check if the comment is top level or a reply
    if comment.is_root:
        # comment is top level comment

        # donload image to ram, fry, save to disk and upload to imgur
        fry_url(comment.submission.url, n)
        uploaded_image_url = helpers.upload_to_imgur()

        # check if the image was uploaded successfully
        if uploaded_image_url is not None:
            # image uploaded successfully
            # try to reply
            for i in range(5):
                try:
                    # upload image and wait a while
                    comment.reply(helpers.gen_reply([uploaded_image_url]))
                    time.sleep(60)
                    return
                except praw.exceptions.APIException as e:
                    # on failure print error and wait one second before retry
                    print(str(e))
                    time.sleep(1)
        else:
            # failed to upload image
            print("Failed to upload image")
            return
    else:
        # comment is a reply

        # find all image urls in parent comment using regex
        urls = re.findall('(https?:\/\/.*\.(?:png|jpg))', comment.parent().body)

        # if no urls found return
        if len(urls) == 0:
            print("\tNo images found.")
            return

        # fry all images found
        fried_urls = []
        for url in urls:
            # fry url and upload result to imgur
            fry_url(url, n)
            url = helpers.upload_to_imgur()

            # check if uploaded successfully
            if url is not None:
                fried_urls.append(url)
            else:
                fried_urls.append('Could not open image.')

        # try to reply
        for i in range(5):
            try:
                comment.reply(helpers.gen_reply(fried_urls))
                time.sleep(60)
                return
            except praw.exceptions.APIException as e:
                print(str(e))
                time.sleep(1)


def login():
    return praw.Reddit(username=config.reddit_username,
                       password=config.reddit_password,
                       client_id=config.reddit_client_id,
                       client_secret=config.reddit_client_secret,
                       user_agent='agent')


if __name__ == '__main__':
    main()
