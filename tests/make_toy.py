"""Dung database mau theo schema `superhero` trong paper (du lieu ngau nhien, KHONG phai BIRD)."""
import json
import random
import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE gender (id INTEGER PRIMARY KEY, gender TEXT);
CREATE TABLE colour (id INTEGER PRIMARY KEY, colour TEXT);
CREATE TABLE race (id INTEGER PRIMARY KEY, race TEXT);
CREATE TABLE publisher (id INTEGER PRIMARY KEY, publisher_name TEXT);
CREATE TABLE alignment (id INTEGER PRIMARY KEY, alignment TEXT);
CREATE TABLE attribute (id INTEGER PRIMARY KEY, attribute_name TEXT);
CREATE TABLE superpower (id INTEGER PRIMARY KEY, power_name TEXT);
CREATE TABLE superhero (id INTEGER PRIMARY KEY, superhero_name TEXT, full_name TEXT,
  gender_id INTEGER, eye_colour_id INTEGER, hair_colour_id INTEGER, skin_colour_id INTEGER,
  race_id INTEGER, publisher_id INTEGER, alignment_id INTEGER, height_cm INTEGER, weight_kg INTEGER,
  FOREIGN KEY (gender_id) REFERENCES gender(id), FOREIGN KEY (eye_colour_id) REFERENCES colour(id),
  FOREIGN KEY (hair_colour_id) REFERENCES colour(id), FOREIGN KEY (skin_colour_id) REFERENCES colour(id),
  FOREIGN KEY (race_id) REFERENCES race(id), FOREIGN KEY (publisher_id) REFERENCES publisher(id),
  FOREIGN KEY (alignment_id) REFERENCES alignment(id));
CREATE TABLE hero_attribute (hero_id INTEGER, attribute_id INTEGER, attribute_value INTEGER,
  FOREIGN KEY (hero_id) REFERENCES superhero(id), FOREIGN KEY (attribute_id) REFERENCES attribute(id));
CREATE TABLE hero_power (hero_id INTEGER, power_id INTEGER,
  FOREIGN KEY (hero_id) REFERENCES superhero(id), FOREIGN KEY (power_id) REFERENCES superpower(id));
"""

G = "SELECT {} FROM superhero AS T1 "
ITEMS = [
    dict(q="How many superheroes have blue eyes?",
         gold="SELECT COUNT(*) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = 'Blue'",
         dummy="SELECT COUNT(*) FROM v_superhero WHERE eye_colour = 'Blue'"),
    dict(q="List the names of Marvel Comics superheroes with blond hair.",
         gold="SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id "
              "INNER JOIN colour AS T3 ON T1.hair_colour_id = T3.id WHERE T2.publisher_name = 'Marvel Comics' AND T3.colour = 'Blond'",
         dummy="SELECT superhero_name FROM v_superhero WHERE publisher_name = 'Marvel Comics' AND hair_colour = 'Blond'"),
    dict(q="List the superpowers of 3-D Man.",
         gold="SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id "
              "INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.superhero_name = '3-D Man'",
         dummy="SELECT power_name FROM v_hero_power WHERE hero_superhero_name = '3-D Man'"),
    dict(q="How many female superheroes have a strength value of 100?",
         gold="SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id "
              "INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id INNER JOIN gender AS T4 ON T1.gender_id = T4.id "
              "WHERE T3.attribute_name = 'Strength' AND T2.attribute_value = 100 AND T4.gender = 'Female'",
         dummy="SELECT COUNT(*) FROM v_hero_attribute WHERE attribute_name = 'Strength' AND attribute_value = 100 AND hero_gender = 'Female'",
         # loi ao giac trong Table 1 cua paper: gan attribute_name cho bang hero_attribute
         s2="SELECT COUNT(*) FROM superhero JOIN hero_attribute ON superhero.id = hero_attribute.hero_id "
            "JOIN gender ON superhero.gender_id = gender.id WHERE hero_attribute.attribute_name = 'Strength' "
            "AND hero_attribute.attribute_value = 100 AND gender.gender = 'Female'"),
    dict(q="How many publishers are there?",
         gold="SELECT COUNT(*) FROM publisher",
         dummy="SELECT COUNT(DISTINCT publisher_id) FROM v_superhero",       # view-only: mat publisher khong co hero
         hybrid="SELECT COUNT(*) FROM publisher"),
    dict(q="How many distinct superpowers do heroes with Intelligence of at least 80 have?",
         gold="SELECT COUNT(DISTINCT T2.power_id) FROM superhero AS T0 INNER JOIN hero_attribute AS T1 ON T0.id = T1.hero_id "
              "INNER JOIN hero_power AS T2 ON T0.id = T2.hero_id INNER JOIN attribute AS T3 ON T1.attribute_id = T3.id "
              "WHERE T3.attribute_name = 'Intelligence' AND T1.attribute_value >= 80",
         dummy="SELECT COUNT(DISTINCT power_id) FROM v_hero_power WHERE hero_id IN (SELECT hero_id FROM v_hero_attribute "
               "WHERE attribute_name = 'Intelligence' AND attribute_value >= 80)"),
    dict(q="What is the average height of superheroes without a publisher?",
         gold="SELECT AVG(height_cm) FROM superhero WHERE publisher_id IS NULL",
         dummy="SELECT AVG(height_cm) FROM v_superhero WHERE publisher_id IS NULL"),
]


def make(root):
    root = Path(root)
    d = root / "dev_databases" / "superhero"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "superhero.sqlite"
    p.unlink(missing_ok=True)
    con, r = sqlite3.connect(p), random.Random(7)
    con.executescript(DDL)
    look = dict(gender=["Male", "Female", "N/A"], colour=["Blue", "Brown", "Green", "Blond", "Black", "Red"],
                race=["Human", "Mutant", "Alien", "Android"], alignment=["Good", "Bad", "Neutral"],
                publisher=["Marvel Comics", "DC Comics", "Dark Horse Comics", "Unused Press"],
                attribute=["Intelligence", "Strength", "Speed"],
                superpower=["Flight", "Agility", "Stealth", "Telepathy", "Super Strength", "Stamina", "Invisibility", "Healing"])
    for t, vals in look.items():
        con.executemany(f"INSERT INTO {t} VALUES (?,?)", list(enumerate(vals, 1)))
    opt = lambda n: r.choice([None] + list(range(1, n + 1)) * 3)
    for i in range(1, 41):
        name = "3-D Man" if i == 1 else f"Hero {i}"
        con.execute("INSERT INTO superhero VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (i, name, f"Full Name {i}", opt(3), opt(6), opt(6), opt(6), opt(4), r.choice([None, 1, 1, 2, 2, 3]),
                     opt(3), r.randint(150, 210), r.randint(50, 120)))
        for a in (1, 2, 3):
            con.execute("INSERT INTO hero_attribute VALUES (?,?,?)", (i, a, r.choice([40, 60, 80, 100])))
        for pw in r.sample(range(1, 9), r.randint(0, 4) if i > 1 else 3):
            con.execute("INSERT INTO hero_power VALUES (?,?)", (i, pw))
    con.commit()
    con.close()
    data = [dict(question_id=i, db_id="superhero", question=it["q"], evidence="", SQL=it["gold"],
                 difficulty=["simple", "moderate", "challenging"][i % 3]) for i, it in enumerate(ITEMS)]
    (root / "toy.json").write_text(json.dumps(data, indent=1))
    script = {}
    for i, it in enumerate(ITEMS):
        script[(i, "base")] = it["gold"]
        script[(i, "s1:oracle:leftover")] = script[(i, "s1:auto:leftover")] = it["dummy"]
        script[(i, "s1:auto:all")] = it.get("hybrid", it["dummy"])
        script[(i, "s2")] = it.get("s2", it["gold"])
    return root / "toy.json", root / "dev_databases", script
