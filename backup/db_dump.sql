-- VaultCore DB dump (parziale) - 14/03/2023
-- ATTENZIONE: contiene hash password. File riservato.

CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);

INSERT INTO users VALUES(1,'alice','8e5f87903be74124026ecdfb9557911a','user');
INSERT INTO users VALUES(2,'bob','12b141f35d58b8b3a46eea65e6ac179e','user');
INSERT INTO users VALUES(3,'carla','37b1f173dc7febe8ce3fb9d8b9d7aeb0','user');
INSERT INTO users VALUES(4,'sysadmin','98e8ba9c3b2cd725856c814cfd4bf7bf','user');
INSERT INTO users VALUES(5,'vcore_admin','fc93fa1e2e5bd6aa8eb6ca5b311b0f64','admin');

-- nota: le password sono MD5 non salato (da migrare a bcrypt, ticket SEC-114)
