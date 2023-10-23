import sqlite3
import os

class DBTools:
    def __init__(self):
        self.dbroot = os.getenv('DBROOT')

        if self.dbroot is None:
            print('ERROR: No DBROOT set in environment')
            return

        if not os.path.exists(f'{self.dbroot}/posts.db'):
            self.connection = sqlite3.connect(f'{self.dbroot}/posts.db')
            cur = self.connection.cursor()
            cur.execute("CREATE TABLE posts(from_id, to_id)")
            cur.close()
            self.connection.commit()
        else:
            self.connection = sqlite3.connect(f'{self.dbroot}/posts.db')


    def add_post(self, from_id, to_id):

        print(f'add_post({from_id}, {to_id})', flush=True)
        cur = self.connection.cursor()
        cur.execute("INSERT INTO posts VALUES (?,?)", (from_id, to_id))
        cur.execute("INSERT INTO posts VALUES (?,?)", (to_id, from_id))
        cur.close()
        self.connection.commit()


    def map_to_other(self, to_id):
        cur = self.connection.cursor()
        cur.execute("SELECT from_id FROM posts where to_id = ?", (to_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


    def dump_db(self):
        cur = self.connection.cursor()
        cur.execute('SELECT * from posts')
        rows = cur.fetchall()
        results = ''
        for row in rows:
            for col in row:
                results += col + ', '
            results += '\n'

        return results





if __name__ == '__main__':
    db = DBTools()
    db.add_post('1', '2')
    db.add_post('3','4')
    print(db.map_to_other('4'))
    print(db.map_to_other('7'))
    print(db.dump_db())
