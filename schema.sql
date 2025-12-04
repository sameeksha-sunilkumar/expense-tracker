CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE budgets (
  id INTEGER PRIMARY KEY,
  category_id INTEGER NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  month TEXT, 
  UNIQUE (category_id, month)
);

CREATE TABLE expenses (
  id INTEGER PRIMARY KEY,
  date DATE NOT NULL,
  category_id INTEGER NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  note TEXT
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE group_members (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    UNIQUE(user_id, group_id)
);

ALTER TABLE expenses ADD COLUMN group_id INTEGER;  
ALTER TABLE expenses ADD COLUMN paid_by_user_id INTEGER;  