'''
Created on 2017. 5. 28.

@author: ssakssri
'''
import sqlite3

conn = sqlite3.connect('tutorial.db')
c = conn.cursor()

def create_table():
    c.execute("CREATE TABLE example (Language VARCHAR, Version REAL, Skill TEXT)")


def enter_data():
    c.execute("INSERT INTO example VALUES('Python', 2.7, 'Beginner')")
    c.execute("INSERT INTO example VALUES('Python', 3.3, 'Intermediate')")
    c.execute("INSERT INTO example VALUES('Python', 3.4, 'Professor')")
    conn.commit()

def enter_dynamic_data():
    lang = input("What language? ")
    version = float(input("Wjat versions? "))
    skill = input("What skill level? ")

    c.execute("INSERT INTO example (Language, Version, Skill) VALUES(?, ?, ?)", (lang, version, skill))

    conn.commit()


def read_from_database():
 

    what_skill = input("What skill level are we looking for? ")
    what_language = input("What lang?")
    sql = "SELECT * FROM example WHERE Skill == ? AND Language == ?"
   
    for row in c.execute(sql,[(what_skill), (what_language)]):
        print(row)

#enter_dynamic_data()
read_from_database()

#conn.close()
