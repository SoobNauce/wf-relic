import sqlite3, read_relics
from typing import List

connection = sqlite3.connect("temp.db")
cursor = connection.cursor()

def rebuild_db():
  cursor.execute("pragma foreign_keys = on;")
  reg = read_relics.read_relics(read_relics.source_table)
  for t in ["relic", "prime", "part", "reward"]:# clear tables
    cursor.execute("drop table if exists {};".format(t))
  
  # relic table
  cursor.execute(
    """create table relic(
      era char(4) not null,
      minor char(3) not null,
      vaulted int not null,
      primary key (era, minor)
    );"""
  )

  # prime table
  # likely optional since prime part contains all known primes
  cursor.execute(
    """create table prime(
      name char(100) primary key
    );"""
  )

  # prime part table
  cursor.execute(
    """create table part(
      base char(100) references prime (name),
      role char(100),
      primary key (base, role)
    );"""
  )

  # reward table
  # n.b. it doesn't care about things that are in there twice
  # so this can't naively be used to calculate probabilities
  cursor.execute(
    """create table reward(
      era char(4) not null,
      minor char(3) not null,

      base char(100) not null,
      role char(100) not null,

      rarity char(10) not null,

      foreign key (era, minor) references relic (era, minor)
      foreign key (base, role) references part (base, role)
      
      primary key (era, minor, base, role, rarity)
    );"""
  )

  # who has which relic at what refinement and how many
  cursor.execute(
      """create table if not exists has_relic (
          player char(100) not null,
          era char(4) not null,
          minor char(3) not null,
          quantity integer not null,
          refinement char(15) not null,

          primary key (player, era, minor, refinement),
          foreign key (era, minor) references relic (era, minor)
      )"""
  )

  # create native helper for relics
  # (era, minor)
  relic_tuples = [tuple(k.split(" ")) for k in reg.relics.keys()]

  # create native helper for primes
  # (name)
  prime_tuples = [(k,) for k in reg.primes.keys()]

  # create native helper for parts
  # (base, role)
  part_tuples = []
  for part_key in reg.parts.keys():
    part_obj = reg.parts[part_key]
    part_tuples.append(
      (part_obj.prime_obj.name,
      part_obj.role)
    )
  
  # create native helper for rewards
  # this one's gonna get messy
  # (era, minor, base, role, rarity)
  # nominally I can use the relic table for all of this
  # it's still terrible
  reward_tuples = []
  for relic_key in reg.relics.keys():
    relic = reg.relics[relic_key]

    era = relic.era
    minor = relic.minor_name

    # these three are lists of objects
    for rarity in ["Common", "Uncommon", "Rare"]:
      for reward in relic.rewards[rarity]:
        base = reward.prime_obj.name
        role = reward.role
        reward_tuples.append(
          (era, minor, base, role, rarity)
        )
  
  cursor.executemany(
    "insert into relic values(?, ?);", relic_tuples
  )

  cursor.executemany(
    "insert into prime values(?);", prime_tuples
  )

  cursor.executemany(
    "insert into part values(?, ?);", part_tuples
  )

  cursor.executemany(
    "insert into reward values(?, ?, ?, ?, ?);", reward_tuples
  )

def rebuild_ownership():
