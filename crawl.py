
import praw
import logging
import mysql.connector
from datetime import datetime, timezone
import os
import pandas as pd
import sys
import pytz



logging.basicConfig(
    filename="/app/logs/crawler.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_secret_from_file(dict, list):
    for var in list:
        try:
            file = os.environ[var + "_FILE"]
            with open(file, "r") as f:
                dict[var] = f.read()
        except Exception as err:
            logging.error(var + err)
    return dict

def validate_secrets(dict, list):
    for var in list:
        if not dict[var] or dict[var] == "":
            return False
    return True

def get_top_posts(reddit, posts):
    subreddit = reddit.subreddit('memes')
    top_posts = subreddit.top(time_filter='day', limit=10)

    logging.info("calling reddit api")
    # posts = []
    # top_set = set()
    for post in top_posts:
        post_data = {
            "post_id": post.id,
            "title" : post.title,
            "score" : post.score,
            "url" : post.url,
            "created_time" : datetime.fromtimestamp(post.created_utc, tz=pytz.timezone("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S"),
            "num_comments" : post.num_comments,
            "author" : str(post.author)
        }
        posts.append(post_data)
        # top_set.add(post.id)

    logging.info("done calling reddit")
    posts = sorted(posts, key= lambda x: x["score"], reverse=True)
    logging.info("sorted")

    return posts


def write_report(posts):
    now = datetime.now(tz=pytz.timezone("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame(posts)
    # df.to_csv(f"/app/out/{now}-table.csv")
    logging.info(f"created data at {now}")
    df.to_csv(f"/app/out/table.csv")


    logging.info("exported to csv")

def save_db(posts, env):
    try:
        logging.info("connecting to sql")
        cnx = mysql.connector.connect(user=env["DB_USER"], password=env["DB_PASSWORD"],
                                host='db',
                                database='db')

        cursor = cnx.cursor()
        stmt = ("INSERT INTO memes (post_id, title, score, url, created_time, num_comments, author) "
                "VALUES (%(post_id)s, %(title)s, %(score)s, %(url)s, %(created_time)s, %(num_comments)s, %(author)s)")

        cursor.executemany(stmt, posts)
        cnx.commit()
        logging.info("committed")
    except Exception as err:
        logging.error(err)

    finally:
        cnx.close()
        logging.info("closed connection to sql")


if __name__ == '__main__':

    logging.info("setting up env")
    env = {}
    secrets = ["DB_PASSWORD", "API_KEY", "API_SECRET"]
    env = get_secret_from_file(env, secrets)
    env["DB_USER"] = os.environ["DB_USER"]

    if not validate_secrets(env, secrets):
        logging.error("secrets invalid")
        sys.exit("secret invalid")
    logging.info(env)
    
    reddit = praw.Reddit(
        client_id=env["API_KEY"],
        client_secret=env["API_SECRET"],
        user_agent='google-colab:meme-crawler'
    )
    
    posts = get_top_posts(reddit, [])
    write_report(posts)
    save_db(posts, env)




# trending_posts = set()
# hot_posts = subreddit.hot(limit=50)
# logging.info(hot_posts)
# for post in hot_posts:
#     if post.id in top_set:
#         trending_posts.add(post.id)



# trending = "\"\n\"Trending memes are: \"\n\""
# for post in trending_posts:
#     trending += post + "\"\n\""
# with open("/app/out/table.csv", "a") as f:
#     f.write(trending)
