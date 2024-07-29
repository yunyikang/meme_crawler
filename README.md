# Meme crawler

## Setup

### Prerequisites

- Docker
- Import secrets folder to root folder (api keys/secret and bot token)

### Build crawler image and run services 

`docker compose up -d --build`

### Stop and remove all services and volumes

`docker compose down -v`

## Overview

![System schematic](./images/diagram.png)

### Tables 

*memes*
- post_id
- author
- create_time
- title 
- url
- PRIMARY KEY (create_time, post_id)

*memes_snaps*
- post_id 
- snap_time
- score
- num_comments 
- PRIMARY KEY (snap_time, post_id)

### Crawler service:
1. Every hour, query top 20 posts from memes subreddit
2. Store new memes into *memes* table
3. Query *memes* to get memes from last 24hrs
4. For each meme, query reddit for its current info (score, num_comments)
5. Store info in *memes_snaps* table
6. Query *memes_snaps* table for 24hr snapshot of top 20 memes
7. Generate report with table and time series graph


### Bot service:
1. Listens for /memes requests
2. Returns the latest report since the hour

### Telegram bot
- user: @yymeme_bot
- type `/memes` to query report

## Report contents
- Time series graph to track performance of each top meme 
- Table of top 20 memes

##  Future improvements
1. Create word cloud of top 20 memes to see if there are trending themes 
2. Summarise meme comments via transformer model to gain more insights on the meme
3. Predict future meme scores via statistical techniques eg ARIMA or transformers with attention blocks eg TimeGPT