#! /usr/bin/env python3
# wf-relic.py
# Ariadne V. Vilece 2019

import sqlite3, read_relics
from typing import List
import tkinter

connection = sqlite3.connect("relics.db")

cursor = connection.cursor()
cursor.execute("pragma foreign_keys = ON")

era_choices = {
  "lith": "Lith",
  "meso": "Meso",
  "neo": "Neo",
  "axi": "Axi",
}
refinement_choices = {
  "intact": "0",
  "exceptional": "1",
  "flawless": "2",
  "radiant": "3",
}

"""sqlite_master is defined in the docs as:

CREATE TABLE sqlite_master (
  type TEXT,
  name TEXT,
  tbl_name TEXT,
  rootpage INTEGER,
  sql TEXT
);

"""

def stopstopstop(text):
  t = tkinter.Tk()
  w = tkinter.Label(t, text=text)
  w.pack()
  t.mainloop()

def soft_prompt(callback: callable):
  # Callback should prompt for some input and then confirm the input afterwards
  x = None
  while True:
    try:
      x = callback()
    except Exception as e:
      prompt = f"Exception {e} received\nDone? [y/any] >>> "
    else:
      prompt = f"Done? [y/any] >>> "
    if input(prompt) == "y":
      break
    else:
      continue
  return x

def format_indices(choice_list: list) -> str:
  # don't need to return choice_list since it already exists as needed
  return (
    "[" +
    ", ".join(
      ["({}, {})".format(choice_list[i], i) for i in range(len(choice_list))]
    ) +
    "]"
  )

def pick_from_dict(choices: dict, title: str, s_es: str = "s"):
  c_list: list = list(choices.keys())# list of possible choices
  # n.b. formatted as the keys of the era or refinement dict, so 
  # hopefully lowercase
  cl_formatted: str = format_indices(c_list)# human-readable
  # pairings of (key, index)
  # uhhh since it's (str, int), and it's going to be read by a human
  # then it doesn't much matter the order...
  print(f"{title} choices: " + cl_formatted)
  cc: str = input("Select by name or index >>> ").lower()# ideally:
  # >>> 1
  # or
  # >>> lith
  # or
  # >>> Lith ((-> lith))
  # same goes for refinements

  if cc in c_list:# already formatted correctly
    # also we can save a call to {}.keys() since we already did that for c_list
    cc_final: str = choices[cc]# the actual capitalized name i.e. Lith
    print(f"Selecting {title} {cc_final} by name")
    return cc_final
  else:# it's not a name, and we can't return early
    # i.e. we have to try to justify it as an index somehow
    ci: int = None
    try:
      ci: int = int(cc)
    except ValueError:
      eve = KeyError(f"{title} {cc} not found in {title} choices " +
        "and can't be justified as a number")
      print(eve)
      raise eve
    if ci < 0 or ci > len(c_list) - 1:
      eve = KeyError(f"{title} index {cc} out of bounds")
      print(eve)
      raise eve
    cc_key: str = c_list[ci]# get the key from the index
    # bounds-checked appropriately above

    cc_final: str = choices[cc_key]# get the era from the key
    # guaranteed by the structure of ec_list

    print(f"Selecting {title} {cc_final} by index")
    return cc_final

def pick_era() -> str:
  return pick_from_dict(
    era_choices, "Era", "s"
  )

def pick_refinement() -> str:
  return pick_from_dict(
    refinement_choices, "Refinement", "s"
  )

def get_players() -> List[str]:
  # Simple select to find players that exist
  rows = cursor.execute("select distinct player from has_relic;").fetchall()
  pcands = [r[0] for r in rows]# oh boy
  # let's unpack that one
  # that sql will return something like
  # [
  #   ('sooby',),
  #   ('capitalthree',)
  # ]
  # so we need that last step to get just the player names
  return pcands

def pick_player():
  pchoices: str = get_players()# this is an ordered list
  # the order doesn't matter in the db so we're still ok

  print("Players: " + format_indices(pchoices))
  pc: str = input("Select a player or enter a new name >>> ")
  if pc in pchoices:
    print(f"Selecting existing player {pc} by name")
    return pc
    # this does mean that if you have a player whose name is a number...
    # ...you can't use that number as an index
    # let's just call that "undefined behavior" for now.
    # ...maybe you can do it with quotes or special handling
  
  try:# Try to justify it as an int
    pindex: int = int(pc)
    player: str = pchoices[pindex]
    print("Selecting existing player {} by index".format(player))
    return player
  except:# I'm not even going to try to handle failure analysis for that one
    print("Creating new player {}".format(player))


def own_one(player: str, era: str, minor: str, quantity: int, refinement: str):
  # player, era, minor, quantity, refinement: string
  # uhhh quantity may need to be cast to an int
  #print("[debug] using the following statement:")
  #print(
  #  "insert or ignore into has_relic values(\n" +
  #  f"{player}, {era}, {minor}, {quantity}, {refinement}\n);"
  #)
  cursor.execute(
"""insert or ignore
  into has_relic
  values (?, ?, ?, ?, ?);""",
  (player, era, minor, quantity, refinement)
  )
  #print("[debug] updating now:")
  #print(
#f"""update has_relic
#  set quantity = {quantity}
#  where player == {player}
#    and era == {era}
#    and minor == {minor}
#    and refinement == {refinement};"""
#  )
  cursor.execute(
"""update has_relic
  set quantity = ?
  where player == ?
    and era == ?
    and minor == ?
    and refinement == ?;""",
    (quantity, player, era, minor, refinement)
  )

def update_ownership(player = None, era = None, refinement = None,
    first_command = None):
  outer_prompt = "[player, era, refinement, entry, done/any] >>> "
  while True:
    if first_command is not None:
      next_command = first_command
      first_command = None
    else:
      next_command = input(outer_prompt).lower()
    if next_command == "player":
      player = pick_player()
      continue
    elif next_command == "era":
      era = pick_era()
      continue
    elif next_command == "refinement":
      refinement = pick_refinement()
      continue
    elif next_command == "entry":
      if player is None:
        print("Need a player. Select one with [player]")
        continue
      if refinement is None:
        print("Need a starting refinement first. Select one with [refinement]")
        continue
      if era is None:
        print("Need a starting era first. Select one with [era]")
        continue
      print("Anything but a valid relic breaks to outer loop")
      print("Optional: era, refinement")
      while True:
        r = input("[era] minor [refinement] quantity (or stop) >>> ").lower()
        if r == "stop": break
        tokens = r.split(" ")
        # format for era: "lith", "Lith", "LITH"
        # format for minor: "G1", "g1"
        # format for refinement: same as era
        # format for quantity: 100
        if len(tokens) < 2:
          print("Can't treat this as a relic")
          break
        try:# gotta deconstruct it in reverse
          # because I'm an idiot and didn't want to reverse it
          # whatever whatever
          quantity = int(tokens.pop())
          if len(tokens) == 1:# "minor quantity" aka "g1 10"
            minor = tokens.pop().upper()
          else:
            mr = tokens.pop()# can't be era because we haven't seen minor yet
            if mr in refinement_choices.keys():
              refinement = mr
              minor = tokens.pop().upper()# minor is mandatory
            else:# can't be era so it must be a minor relic name
              minor = mr.upper()
          # finally, we've seen quantity, minor, and refinement
          # so there's only era left
          # I want to go soak my head
          if len(tokens) == 1:# the only thing left is era
            era = tokens.pop()
          elif len(tokens) > 1:# We should have popped minor before
            # so we shouldn't be left with anything
            raise ValueError("Too many identifiers")
          # if len(tokens) == 0, then we already popped everything we need to
        except IndexError:# always gonna be pop from empty list here
          print("Not enough identifiers\nBreaking to outer loop")
          break
        except ValueError as ve:
          print(f"Couldn't parse. {ve}")
          break
        # now the fun part: sanity checking.
        # so far we need player, era, minor, quantity, refinement

        # let's do player first
        all_players = get_players()
        if player in all_players:
          print(f"Using existing player {player}")
        else:
          print(f"Adding new player {player}")
        # Can't really do sanity checking on it so let's move on

        # next, let's do era
        e_rows = cursor.execute("select distinct era from relic").fetchall()
        all_eras = [r[0] for r in e_rows]
        if era in all_eras:
          print(f"Selecting valid era {era}")
        elif era.lower() in era_choices.keys():
          era = era_choices[era.lower()]
          print(f"Fixing caps, selecting valid era {era}")
        else:
          print(f"Unknown era {era}")
          continue
        
        # ok ok let's do minor next
        # the structure of minor is [rare_reward_first_initial][generation]
        # i.e. G + 10
        # I can't guarantee generation will be 1 digit
        # but I CAN guarantee that the first initial is 1 digit.
        if len(minor) == 0:
          print("Empty minor revision")
          continue
        minor_fi: str = minor[0]
        minor_rev: str = minor[1:]
        if len(minor_rev) == 0:
          print(f"Empty minor revision for minor string {minor}")
          continue
        try:
          minor_i = int(minor_rev)
        except ValueError:
          print(f"Can't coerce minor_rev {minor_rev} into an int")
          continue
        print(f"Rare reward first initial: {minor_fi}")
        print(f"Minor revision: {minor_i}")
        # the name is still G10 or whatever
        # so we can discard minor_fi and minor_i now
      
        # ok that was fun, we gotta do quantity next.
        if quantity < 0:
          print(f"Negative quantity {quantity}. Enter the actual number owned or 0")
          continue
        # It was already int-checked above for some reason
        # so the non-negative is the only check we need here
        print(f"Quantity: {quantity}")

        # Finally, at long last, it's time to check refinement
        # there's actually nothing in the database for refinement
        # so we've gotta enforce it from the dict.
        if refinement not in refinement_choices.values():
          rl = refinement.lower()
          if rl not in refinement_choices.keys():
            print(f"Can't find refinement {refinement}")
            continue
          else:
            refinement = refinement_choices[rl]
            print(f"Capitalizing and using refinement {refinement}")
        else:
          print(f"Using refinement {refinement}")
         
        # Now, at long, long last, we're ok to add to the table.
        # One last "ok" prompt.
        print(
          ("[debug] Want to insert \n" +
            "({}, {}, {}, {}, {}) into has_relic\n" +
              "(player, era, minor, quantity, refinement)").format(
            player, era, minor, quantity, refinement
          )
        )
        prompt = False
        if prompt:
          if input("Ok? [y/any] >>> ") == "y":
            own_one(player, era, minor, quantity, refinement)
        else:
            own_one(player, era, minor, quantity, refinement)
    else:# context: "if next_command ==......"
      break

def unpack_table(table_from_sql):
  tfs = table_from_sql
  s_rows = [
    [
      str(c) for c in r
    ]
    for r in tfs
  ]
  formatted_rows = "\n".join(
    [
      "\t".join(
        [c for c in r]
      )
      for r in s_rows
    ]
  )
  return formatted_rows

def dq():# debug: quick view has_relic
  hr_rows = cursor.execute(
    "select * from has_relic order by era asc, quantity desc;"
  ).fetchall()
  return unpack_table(hr_rows)

def du(fe):# debug: quick update ownership
  update_ownership("sooby", fe, "0", "entry")

# helpful: cursor.execute("select * from sqlite_master")

def update_vaulteds():
  reg = read_relics.read_relics(read_relics.source_table)
  uvr = [
    (rel.vaulted, rel.era, rel.minor_name)
    for rel in reg.relics.values()
  ]
  cursor.executemany(
    "update relic set vaulted = ? where era == ? and minor == ?",
    uvr
  )

if __name__ == "__main__":
  pass
  #update_vaulteds()
  #connection.commit()
