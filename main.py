import praw
import praw.exceptions
import prawcore.exceptions
import config
import time
import re
import helpers
import settings
import threading
from frying import fry_url


# TODO: Improve command line output


def main():
    # list of subreddits to be tracked without username mention
    subreddits = ['comedycemetery', 'memes', 'DeepFriedMemes',
                  'nukedmemes', 'ComedyNecrophilia', 'dankmemes']

    # login to reddit and enter main loop
    reddit = login()
    sub = reddit.subreddit('+'.join(subreddits))
    while True:
        # load settings
        settings_dict = settings.loadSettings('./settings.txt')

        # check and fry username mentions
        check_mentions(reddit)

        # check and fry comments
        # get comments from subreddits
        try:
            comments = list(sub.comments(limit=settings_dict['max_comments']))
        except Exception as e:
            print(str(e))
            continue

        for comment in comments:
            # thread = threading.Thread(target=check, args=[comment])
            # thread.start()
            check(comment)

        # All comments processed, wait for some time before rechecking
        time.sleep(settings_dict['check_delay'])


def check_mentions(reddit):
    # try to get username mentions
    try:
        mentions = list(reddit.inbox.mentions(limit=10))
    except Exception as e:
        print(str(e))
        return

    # check mentions for requests
    for comment in mentions:
        # thread = threading.Thread(target=check, args=[comment])
        # thread.start()
        check(comment)


# verify that comment hasn't been changed
def final_check(comment):
    text = helpers.remove_specials(comment.body)
    if 'morefrying' in text:
        return True
    elif 'morenuking' in text:
        return True
    else:
        return False


# check comment for frying request
def check(comment):
    # string for holding the message a thread prints when it finishes
    output = ''

    # Ignore too long comments
    if len(comment.body) > 500:
        return

    # remove special characters and change to lower case
    text = helpers.remove_specials(comment.body)

    # determine type of request
    if 'morefrying' in text:
        message = "Post needs more frying!\n"
        n = 1
    elif 'morenuking' in text:
        message = "Post needs more nuking!\n"
        n = 5
    else:
        # print("No frying requested.")
        return

    # fetch comment replies
    try:
        comment.refresh()
        comment.replies.replace_more(limit=0)
    except Exception as e:
        print("Failed to get comment replies.")
        return

    # verify that the request hasn't been fulfilled
    for reply in comment.replies:
        if reply.author.name == 'DeepFryBot':
            output += "Frying request already fulfilled.\n"
            print(output)
            return

    # verify that the post is quality is adequate to reduce spam
    output += "Checking post quality:\n"
    try:
        ratio = comment.submission.upvote_ratio
        ups = comment.submission.ups
    except Exception as e:
        output += "\t\tFailed to check post quality."
        print(output)
        return
    output += "\tRatio of upvotes to downvotes: {0}\n".format(ratio)
    if ratio < 0.70:
        output += "\t\tRatio too low. Skipping post.\n"
        print(output)
        return
    output += "\tNumber of upvotes: {0}\n".format(ups)
    if ups < 5:
        output += "\t\tToo few upvotes. Skipping post.\n"
        print(output)
        return
    output += "\tPost is OK.\n"

    # display the request type
    output += message

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
                    # verify that the comment requesting frying hasn't been changed
                    if final_check(comment) is not True:
                        print(output)
                        return

                    # reply to request
                    comment.reply(helpers.gen_reply([uploaded_image_url]))
                    print(output)
                    return
                except prawcore.exceptions.Forbidden:
                    # If response is 'forbidden' the bot is probably banned so there is no sense to retry.
                    output += "Commenting forbidden. Bot probably banned from /r/{0}\n".format(comment.subreddit)
                    print(output)
                    return
                except Exception as e:
                    # on failure print error and wait some time before retrying
                    output += str(e)
                    time.sleep(5)
        else:
            # failed to upload image
            output += "Failed to upload image\n"
            print(output)
            return
    else:
        # comment is a reply

        # disable chained frying
        return

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
                if final_check(comment) is not True:
                        return
                comment.reply(helpers.gen_reply(fried_urls))
                time.sleep(30)
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
