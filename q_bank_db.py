#!/usr/bin/python3.7
import pymysql.cursors
from pymysql.err import Error
import os

class DB:
    cred = {
        'host': '127.0.0.1',
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWD', 'password'),
        'db': os.environ.get('DB_PASSWD', 'dc_db'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    QUERIES = {
        'SQL_GET_A_QUES_DIFF': "select * from `q_bank` where `difficulty` = %s and `isdone` = false order by rand() limit 1;",
        'SQL_GET_A_QUES_TAG': "select * from `q_bank` where `isdone` = false and `tags` like %s order by rand() limit 1;",
        'SQL_GET_A_QUES_DIFF_TAG': "select * from `q_bank` where `isdone` = false and  `difficulty` = %s and `tags` like %s order by rand() limit 1;",
        'SQL_SET_DONE': "update `q_bank` set `isdone`=true where id=%s;",
        'SQL_GET_HINT': "select hints, tags from `q_bank` where id = %s;"
    }

    def __init__(self, **kwargs):
        self.cred.update(kwargs)
        self.connection = None

    def _check_connection(self):
        if not self.connection:
            raise Error("No DBConnection established. use .connect first")

    def connect(self):
        if not self.connection:
            self.connection = pymysql.connect(**self.cred)

    def close(self):
        if not self.connection:
            return
        self.connection.close()
        self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_value is None:
            self.connection.commit()
        self.connection.close()

    def get_ques(self, diff=None, tag=None):
        self._check_connection()
        with self.connection.cursor() as cursor:
            q = 'SQL_GET_A_QUES'
            para = []
            if diff is not None:
                q += '_DIFF'
                para.append(diff)
            if tag:
                tag = f"%{tag}%"
                q += '_TAG'
                para.append(tag)

            if cursor.execute(self.QUERIES.get(q), tuple(para)):
                return cursor.fetchone()
            else:
                return None

    def update_ques_content(self, content, id):
        self._check_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(self.QUERIES.get('SQL_UPDATE_CONTENT'), content, id)

    def after_posted(self, qid):
        self._check_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(self.QUERIES.get('SQL_SET_DONE'), qid)

    def get_hint(self, qid):
        self._check_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(self.QUERIES.get('SQL_GET_HINT'), qid)
            return cursor.fetchone()
