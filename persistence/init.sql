CREATE DATABASE chan;

CREATE TABLE changrid (
  position INT NOT NULL,
  image VARCHAR(256) NOT NULL,
  thumb VARCHAR(256) NOT NULL,
  commentid INT NOT NULL,
  summary TEXT NOT NULL,
  last_seen TIMESTAMP NOT NULL,
  PRIMARY KEY (position)
);

INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (0, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (1, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (2, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (3, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (4, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (5, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (6, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (7, '', '', 0, '', TIMESTAMP '2000-01-01');
INSERT INTO changrid (position, image, thumb, commentid, summary, last_seen) VALUES (8, '', '', 0, '', TIMESTAMP '2000-01-01');

CREATE TABLE chanfavs (
  commentid INT NOT NULL,
  image VARCHAR(256) NOT NULL,
  thumb VARCHAR(256) NOT NULL,
  summary TEXT NOT NULL,
  userid INT NOT NULL,
  time TIMESTAMP NOT NULL,
  PRIMARY KEY (commentid)
);

CREATE TABLE blacklist (
  comment_id INT NOT NULL,
  PRIMARY KEY (comment_id)
);
