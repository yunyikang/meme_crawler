DROP TABLE IF EXISTS memes;
CREATE TABLE memes (
  post_id VARCHAR(256) NOT NULL,
  title VARCHAR(256) NOT NULL,
  url VARCHAR(256) NOT NULL,
  author VARCHAR(256) NOT NULL,
  create_time DATETIME NOT NULL,
  PRIMARY KEY (create_time, post_id)
);

DROP TABLE IF EXISTS meme_snaps;
CREATE TABLE meme_snaps (
  post_id VARCHAR(256) NOT NULL,
  score INT NOT NULL,
  num_comments INT NOT NULL,
  snap_time DATETIME NOT NULL,
  PRIMARY KEY (snap_time, post_id)
);


-- CREATE TABLE memes (
--   id INT NOT NULL AUTO_INCREMENT,
--   post_id VARCHAR(256) NOT NULL,
--   title VARCHAR(256) NOT NULL,
--   score INT NOT NULL,
--   url VARCHAR(256) NOT NULL,
--   created_time DATETIME NOT NULL,
--   num_comments INT NOT NULL,
--   author VARCHAR(256) NOT NULL,
--   PRIMARY KEY (id)
-- );