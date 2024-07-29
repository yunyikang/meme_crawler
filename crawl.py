
import praw
import logging
import mysql.connector
from datetime import datetime, timedelta
import os
import pandas as pd
import sys
import pytz
import matplotlib.pyplot as plt
import dataframe_image as dfi
from spire.doc import *
from spire.doc.common import *



logging.basicConfig(
    filename="/app/logs/crawler.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

mlogger = logging.getLogger('matplotlib')
mlogger.setLevel(logging.WARNING)

colors = [ '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
          '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', 
          '#008080', '#e6beff', '#9a6324', '#800000', '#aaffc3',  
          '#808000', '#ffd8b1', '#000075', '#808080', '#000000' ]

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
    top_posts = subreddit.top(time_filter='day', limit=20)

    logging.info("calling reddit api")

    for post in top_posts:
        post_data = {
            "post_id": post.id,
            "author" : str(post.author),
            "title" : post.title,
            "url" : post.url,
            "score" : post.score,
            "num_comments" : post.num_comments,
            "create_time" : datetime.fromtimestamp(post.created_utc, tz=pytz.timezone("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S")
        }
        posts.append(post_data)

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
        # stmt = ("INSERT INTO memes (post_id, title, score, url, create_time, num_comments, author) "
        #         "VALUES (%(post_id)s, %(title)s, %(score)s, %(url)s, %(create_time)s, %(num_comments)s, %(author)s)")

        stmt = ("INSERT INTO memes (post_id, title, url, author, create_time) "
                "VALUES (%(post_id)s, %(title)s, %(url)s, %(author)s, %(create_time)s)")


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

    # 1. get top posts
    # 2. create df and modify fields (create time and num_comments)
    # 3. export to df
    # 4. save new posts to to db
    # 5. query past 24 hr posts
    # 6. call reddit.info on the posts 
    # 7. insert snap shots in meme_snaps
    # 8. query meme_snaps for past 24hr snapshots
    # 9. plot time series
    # 10. create pdf and attach table and timeseries 

    top_posts = get_top_posts(reddit, [])

    #save top_post to image
    df = pd.DataFrame(top_posts)
    #format datetime to exclude years
    logging.info("changing time format")
    df = df.rename(columns={"num_comments" : "comments"})
    df['create_time'] = pd.to_datetime(df['create_time'])
    df["create_time"] = df["create_time"].dt.strftime("%m-%d %H:%M")

    logging.info("changed time format")

    dfi.export(df, '/app/out/table.png',table_conversion='matplotlib')

    
    top_post_ids = [p["post_id"] for p in top_posts]
    try:

        cnx = mysql.connector.connect(user=env["DB_USER"], password=env["DB_PASSWORD"],
                                    host='db',
                                    database='db')

        cursor = cnx.cursor()

        
        #save new memes to memes
        stmt = ("INSERT IGNORE INTO memes (post_id, title, url, author, create_time) "
                "VALUES (%(post_id)s, %(title)s, %(url)s, %(author)s, %(create_time)s)")


        cursor.executemany(stmt, top_posts)
        cnx.commit()    
        logging.info("committed new top memes")        
        
        #query memes for last 24 hr memes
        query = ("SELECT post_id FROM memes "
                "WHERE create_time BETWEEN %s AND %s")
        
        now = datetime.now(tz=pytz.timezone("Asia/Singapore")) #.strftime("%Y-%m-%d %H:%M:%S")
        start = now - timedelta(hours=24)

        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        logging.info(now_str)        
        logging.info(start_str)        

        cursor.execute(query, (start_str, now_str))
        
        logging.info("2")        

        l = []
        for post_id in cursor:
            l.append("t3_" + post_id[0])
        
        logging.info(l)        

        #call reddit api for snapshots of ids'
        post_list = []
        posts = reddit.info(fullnames=l)
        for post in posts:
            post_data = {
                "post_id": post.id,
                "score" : post.score,
                "num_comments" : post.num_comments,
                "snap_time" : datetime.now(tz=pytz.timezone("Asia/Singapore")).replace(microsecond=0, second=0, minute=0).strftime("%Y-%m-%d %H:%M:%S")
                # "snap_time" : datetime.now(tz=pytz.timezone("Asia/Singapore")).replace(microsecond=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
            }
            post_list.append(post_data)
        
        # logging.info(post_list)
        stmt = ("INSERT IGNORE INTO meme_snaps (post_id, score, num_comments, snap_time) "
                "VALUES (%(post_id)s, %(score)s, %(num_comments)s, %(snap_time)s)")


        cursor.executemany(stmt, post_list)
        cnx.commit()
        logging.info("committed meme snaps")

        #query meme snaps
        placeholders = ', '.join("%s" for i in top_posts)

        query = ("SELECT post_id, score, snap_time FROM meme_snaps "
                "WHERE post_id IN (%s) AND snap_time BETWEEN %%s AND %%s") % placeholders  
        
        # now = datetime.now(tz=pytz.timezone("Asia/Singapore")).replace(microsecond=0, second=0, minute=0) 
        # now = datetime.now(tz=pytz.timezone("Asia/Singapore")).replace(microsecond=0, second=0) 
        # start = now - timedelta(hours=24)

        logging.info(query)
        logging.info(tuple(top_post_ids) + (start_str, now_str))

        cursor.execute(query, tuple(top_post_ids) + (start_str, now_str))
                      
        snaps = []
        for (post_id, score, snap_time) in cursor:
            snap_data = {
                "post_id" : post_id,
                "score" : score,
                "snap_time" : snap_time
            }
            snaps.append(snap_data)

        logging.info(len(snaps))
        df = pd.DataFrame(snaps)
        logging.info(df)

        df = df=df.astype({"snap_time":"datetime64[ns]"})

        timeslots = sorted(df['snap_time'].unique())
        logging.info(timeslots)

        for id in top_post_ids:
            time_set = set(df.loc[df['post_id']==id]["snap_time"].unique())
            for slot in timeslots:
                if slot not in time_set:
                    row = pd.DataFrame({"post_id" : [id], "score" : [None], "snap_time" : [slot]})
                    df = pd.concat([df, row], ignore_index=True)
                    
        logging.info(df)
        logging.info([(p["post_id"], p["create_time"]) for p in top_posts])


        fig, (ax, ax1) = plt.subplots(nrows=2, ncols=1)
        # timeslots = [i.strftime("%H:%M") for i in timeslots]
        timeslots = [i.strftime("%-I%p") for i in timeslots]

        color_idx = 0
        for id in top_post_ids:
            scores = df.loc[df['post_id']==id].sort_values(["snap_time"])["score"].to_list()
            #select color
            ax.plot(timeslots, scores, color=colors[color_idx], linestyle="-.", marker="o")
            ax1.plot(timeslots, scores, color=colors[color_idx], linestyle="-.", marker="v")
            color_idx += 1

        logging.info("here")

        ax.set_title("Scores over the past 24hrs")
        ax.set_xlabel("Hour")
        ax.set_ylabel("Score")
        ax.grid(True)

        ax1.set_yscale('log')
        ax1.set_xlabel("Hour")
        ax1.set_ylabel("log Score")
        ax1.grid(True)

        fig.legend(top_post_ids, loc="lower center", bbox_to_anchor=(0.5, -0.1), fancybox=True, shadow=True, ncol=5)         
        fig.tight_layout(pad=1.5)
        fig.set_size_inches(8, 8.5, forward=True)
        fig.savefig('/app/out/timeseries.png', bbox_inches='tight')
        # bbox_extra_artists=(lgd,),

        logging.info("creating doc")

        document = Document()
        section = document.AddSection()
        
        titleParagraph = section.AddParagraph()
        title = titleParagraph.AppendText("Memes Report")
        # title.CharacterFormat.FontSize = 12
        titleParagraph.ApplyStyle(BuiltinStyle.Heading1)
        titleParagraph.Format.AfterSpacing = 5
        titleParagraph.Format.HorizontalAlignment = HorizontalAlignment.Center

        now = datetime.now(tz=pytz.timezone("Asia/Singapore")).replace(microsecond=0, second=0, minute=0).strftime("%-d %b %-I%p")
        paragraph1 = section.AddParagraph()
        tr1 = paragraph1.AppendText(f"Last update at {now}")
        # tr1.CharacterFormat.FontName = "Calibri"
        tr1.CharacterFormat.Size = 2
        paragraph1.Format.AfterSpacing = 10
        paragraph1.Format.HorizontalAlignment = HorizontalAlignment.Right        

        imgPara2 = section.AddParagraph()
        picture = imgPara2.AppendPicture("/app/out/timeseries.png")
        imgPara2.Format.HorizontalAlignment = HorizontalAlignment.Left
        # picture.Width = 300
        # picture.Height = 300
        # imgPara2.Format.AfterSpacing = 100
        # imgPara2.Format.BeforeSpacing = 30
        imgPara2.AppendBreak(BreakType.PageBreak)
        logging.info("doc 2")

        paragraph = section.AddParagraph()
        tr = paragraph.AppendText("Top 20 memes in the past 24hrs")
        # tr.CharacterFormat.FontName = "Calibri"
        tr.CharacterFormat.FontSize= 16
        paragraph.Format.AfterSpacing = 10
        paragraph.Format.HorizontalAlignment = HorizontalAlignment.Center

        imgPara = section.AddParagraph()
        picture = imgPara.AppendPicture("/app/out/table.png")
        picture.Width = 260
        picture.Height = 250
        # picture.TextWrappingStyle = TextWrappingStyle.Through
        imgPara.Format.HorizontalAlignment = HorizontalAlignment.Center
        imgPara.Format.AfterSpacing = 20 
        # imgPara.AppendBreak(BreakType.PageBreak)
        logging.info("doc 1")

        


        document.SaveToFile("/app/out/report.pdf", FileFormat.PDF)

        now = datetime.now(tz=pytz.timezone("Asia/Singapore")).strftime("%Y-%m-%d-%H-%M-%S")
        document.SaveToFile(f"/app/out/report-{now}.pdf", FileFormat.PDF)

        # document.SaveToFile("/test_doc.docx", FileFormat.Docx)
        document.Close()
        logging.info("created doc")

        
        # write_report(top_posts)
        # save_db(posts, env)

    except Exception as err:
        logging.error(err)

    finally:
        cnx.close()
        logging.info("closed connection to sql")

