import sqlite3
import os

class DBTools:
    def __init__(self):
        self.dbroot = os.getenv('DBROOT')
        if not os.path.exists(f'{self.dbroot}/posts.db'):
            self.connection = sqlite3.connect(f'{self.dbroot}/posts.db')
            cur = self.connection.cursor()
            cur.execute("CREATE TABLE posts(from_id, to_id)")
            cur.close()
            self.connection.commit()
        else:
            self.connection = sqlite3.connect(f'{self.dbroot}/posts.db')


    def add_post(self, from_id, to_id):
        cur = self.connection.cursor()
        cur.execute("INSERT INTO posts VALUES (?,?)", (from_id, to_id))
        cur.close()
        self.connection.commit()


    def source_to_trans(self, to_id):
        cur = self.connection.cursor()
        cur.execute("SELECT from_id FROM posts where to_id = ?", (to_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]

    def trans_to_source(self, from_id):
        cur = self.connection.cursor()
        cur.execute("SELECT to_id FROM posts where from_id = ?", (from_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]




if __name__ == '__main__':
    db = DBTools()
    db.add_post('1', '2')
    db.add_post('3','4')
    print(db.source_to_trans('4'))
    print(db.source_to_trans('7'))