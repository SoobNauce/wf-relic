#! /usr/bin/python
# wfrelic-updatedb.py
# Ariadne Vilece, 2019

# Updates relic database to reflect new vaulted status
# considering how DE does things, it should
# require a major rewrite, bordering on being impossible
# to update an existing relic in any way other than
# making it vaulted or unvaulted

import sqlite3, read_relics
from typing import List

connection = sqlite3.connect("temp.db")# do work in temp db
# until it's ready for primetime
cursor = connection.cursor()

make_changes = True# very important

def get_relic_updates(registry, db_cursor):
    good_relics = []# Relics that do not need to be updated
    vaulting_relics = []# Relics that need their vaulting status updated
    new_relics = []# Relics that need to be added
    bad_relics = []# Relics that failed verification
    missing_relics = []# Relics that don't appear in the table
    # (VERY BAD)
    for r_key in registry.relics.keys():
        # In case a relic is somehow removed, I'm going to
        # check both directions
        # exists r such that r in reg and r not in relics_table
        # exists r such that r in relics_table and r not in reg
        # when in doubt, trust reg
        # which is a scary prospect
        # because of the integrity constraints
        # basically, anything except those two better have a good reason
        # and is worth doing manually
        relic = registry.relics[r_key]
        entries_in_db = db_cursor.execute("select * from relic " +
            "where era = ? and minor = ?", 
            (relic.era, relic.minor_name)
        ).fetchall()
        # debug
        if len(entries_in_db) == 0:# Relic is in registry but not database
            # HOPEFULLY means there's a new relic added
            new_relics.append(r_key)
        elif len(entries_in_db) == 1:
            edb = entries_in_db[0]
            vaulted_case = (edb[2], relic.vaulted)
            #if vaulted_case == (0,0):
            #    #print("\tBoth say unvaulted")
            #    pass
            #elif vaulted_case == (1,1):
            #    #print("\tBoth say vaulted")
            #    pass
            #elif vaulted_case == (1,0):
            #    print("\tRelic has become unvaulted")
            #elif vaulted_case == (0,1):
            #    print("\tRelic has become vaulted")
            #else:
            #    print("\tWas {0}, is now {1}".format(*vaulted_case))
            if vaulted_case[0] == vaulted_case[1]:
                # Doesn't need to be updated
                good_relics.append(r_key)
            else:
                vaulting_relics.append(
                    (r_key, vaulted_case[0], vaulted_case[1])
                )
        else:
            #print(f"Too many results for this relic?\n\t", end="")
            #print( "\n\t".join(entries_in_db) )
            bad_relics.append(r_key)
    __test__all_relics_in_db = db_cursor.execute(
"""select * from relic;"""
    ).fetchall()
    for relic_row in __test__all_relics_in_db:
        rr_era = relic_row[0]
        rr_minor = relic_row[1]
        rr_name = f"{rr_era} {rr_minor}"
        if rr_name not in registry.relics.keys():
            missing_relics.append(relic_row)
            #print(f"Relic row {relic_row} not found in registry")
    # new_relics is a list of relic names
    # vaulting_relics is a list of relic names along with their old/new status
    # good_relics is a list of relic names
    # bad_relics is a list of relic names
    # missing_relics is a list of relic ROW entries from the database
    
    # new, good, vaulting, bad
    new_relics.sort()
    vaulting_relics.sort()
    good_relics.sort()
    bad_relics.sort()
    missing_relics.sort()
    #print("New relics (in reg but not in db):\n\t" +
    #    ", ".join(new_relics))
    #print("Relics that need vaulted status updated:\n\t" +
    #    ", ".join(
    #        ["{} (was {}, now {})".format(*cr) for cr in vaulting_relics]))
    #print("Relics that don't need to be updated:\n\t" +
    #    ", ".join(good_relics))
    #print("Relics that returned bad results:\n\t" +
    #    ", ".join(bad_relics))
    #print("Relics that used to exist but are no longer in the given table:\n\t" +
    #    "[era, minor, vaulted]\n\t" + 
    #    "\n\t".join([str(m) for m in missing_relics]))
    return {
        "new": new_relics,
        "vaulting": vaulting_relics,
        "existing": good_relics,
        "bad": bad_relics,
        "removed": missing_relics
    }

def get_prime_updates(registry, db_cursor):
    new_primes = []# good
    removed_primes = []# bad
    existing_primes = []# ones with no change
    bad_primes = []
    for prime_key in registry.primes.keys():
        # In this case, the prime object in the db
        # might as well not exist
        # so we don't need to check too much here
        db_entry = db_cursor.execute(
            "select * from prime where name = ?",
            (prime_key,)).fetchall()
        if len(db_entry) == 0:# Prime in table and not in db
            # i.e. a new prime
            new_primes.append(prime_key)
        elif len(db_entry) == 1:# prime in table and in db
            # i.e. no update needed
            existing_primes.append(prime_key)
        else:# two or more? problematic...
            bad_primes += db_entry# it's a list filled with row entries
            # so you can use += to append each of them
    __test__all_primes_in_db = db_cursor.execute("select * from prime").fetchall()
    for prime_row in __test__all_primes_in_db:
        if prime_row[0] not in registry.primes.keys():# prime_row[0] is
            # the name itself
            # if it's not in the registry, something's gone wrong because primes should
            # never DISAPPEAR during an update.
            removed_primes.append(prime_row[0])
    new_primes.sort()# prime names
    removed_primes.sort()# prime ROWS
    existing_primes.sort()# prime names
    bad_primes.sort()# prime ROWS
    #print("New primes (in reg but not db):\n\t" +
    #    ", ".join(new_primes))
    #print("Removed primes (bad! none should be removed.):\n\t" +
    #    "\n\t".join([str(r) for r in removed_primes]))
    #print("Primes that don't need to be updated:\n\t" +
    #    ", ".join(existing_primes))
    #print("Primes that have two or more entries in the database:\n\t" +
    #    "\n\t".join([str(b) for b in bad_primes]))
    return {
        "new": new_primes,
        "removed": removed_primes,
        "existing": existing_primes,
        "bad": bad_primes
    }

def get_part_updates(registry, db_cursor):
    new_parts = []# good
    removed_parts = []# bad
    existing_parts = []# ok
    bad_parts = []# obviously
    for part_key in registry.parts.keys():
        part_obj = registry.parts[part_key]
        prime_name = part_obj.prime_obj.name
        part_role = part_obj.role
        db_entry = db_cursor.execute(
            "select * from part where base = ? and role = ?",
            (prime_name, part_role)
        ).fetchall()
        if len(db_entry) == 0:
            new_parts.append(part_key)
        elif len(db_entry) == 1:
            existing_parts.append(part_key)
        else:
            bad_parts += db_entry
    __test__all_parts_in_db = db_cursor.execute("select * from part").fetchall()
    for part_row in __test__all_parts_in_db:
        part_key = part_row[0] + " " + part_row[1]
        if part_key not in registry.parts.keys():
            removed_parts.append(part_row)
    new_parts.sort()
    removed_parts.sort()
    existing_parts.sort()
    bad_parts.sort()
    #print("New parts:\n\t" +
    #    ", ".join(new_parts))
    #print("Removed parts:\n\t" +
    #    "\n\t".join([str(r) for r in removed_parts]))
    #print("Parts to leave alone:\n\t" +
    #    ", ".join(existing_parts))
    #print("Parts that have two or more entries:\n\t" +
    #    "\n\t".join([str(b) for b in bad_parts]))
    return {
        "new": new_parts,
        "removed": removed_parts,
        "existing": existing_parts,
        "bad": bad_parts
    }

def get_reward_updates(registry, db_cursor):
    # this one's gonna be bad
    new_rewards = []
    removed_rewards = []
    existing_rewards = []
    bad_rewards = []
    all_rewards = []# expensive
    for relic_key in registry.relics.keys():
        relic = registry.relics[relic_key]
        for reward_rarity in ["Common", "Uncommon", "Rare"]:
            for part_obj in relic.rewards[reward_rarity]:
                reward_tuple = (
                    relic.era,
                    relic.minor_name,
                    part_obj.prime_obj.name,
                    part_obj.role,
                    reward_rarity
                )
                all_rewards.append(reward_tuple)
                from_db = cursor.execute(
                    """select * from reward
                    where
                        era = ? and
                        minor = ? and
                        base = ? and
                        role = ? and
                        rarity = ?""",
                    reward_tuple
                ).fetchall()
                if len(from_db) == 0:
                #    print(reward_tuple)
                    new_rewards.append(reward_tuple)
                elif len(from_db) == 1:
                    existing_rewards.append(reward_tuple)
                elif len(from_db) > 1:
                #    print(reward_tuple)
                #    print("\n".join([str(f) for f in from_db]))
                    bad_rewards += from_db
    __test__all_rewards_in_db = db_cursor.execute(
        "select * from reward").fetchall()
    for reward_row in __test__all_rewards_in_db:
        if reward_row not in all_rewards:
            removed_rewards.append(reward_row)
    return {
        "new": new_rewards,
        "removed": removed_rewards,
        "existing": existing_rewards,
        "bad": bad_rewards,
        "all": all_rewards
    }


if __name__ == "__main__":
    cursor.execute("pragma foreign_keys = on;")
    reg = read_relics.read_relics(read_relics.source_table)
    # Now it's time to find out what changes we'll be making
    updates = {
        "relic": get_relic_updates(reg, cursor),
        # hopefully only contains new relics and updated vaulted status
        "prime": get_prime_updates(reg, cursor),
        # hopefully only contains new primes
        # ...I hope there aren't any primes that get removed...
        "part": get_part_updates(reg, cursor),
        # same as above, new prime parts and
        # HOPEFULLY nothing got removed.
        "reward": get_reward_updates(reg, cursor)
        # hopefully only contains new entries
        # ...I hope that no rewards get changed...
    }
    for update_key in updates.keys():
        print(update_key)
        full_update = updates[update_key]
        new = full_update["new"]
        removed = full_update["removed"]
        if len(removed) > 0:
            print("removed:\n\t" + 
                "\n\t".join([str(r) for r in removed]))
            raise Exception("Relics were removed.")
        existing = full_update["existing"]
        bad = full_update["bad"]
        if len(bad) > 0:
            print("bad:\n\t" +
                "\n\t".join([str(b) for b in bad]))
            raise Exception("There are bad relics.")
        print(f"Checking updates for class {update_key}")
        print(f"\t{len(new)} new\n" +
            f"\t{len(removed)} removed\n" +
            f"\t{len(existing)} not to update\n" +
            f"\t{len(bad)} bad")
    to_update_vaulting = updates["relic"]["vaulting"]
    print(f"Additionally, {len(to_update_vaulting)} relics to update vaulted status")
    # let's get started
    # Above, we guaranteed no entries are removed.
    # We also guaranteed no bad entries.
    # We also have some that don't need to be updates.
    # All we need to update is "new" and "vaulting".
    if make_changes == True:
        for rupdate_key in updates["relic"]["new"]:# do relics first
            # since they don't dpend on anything
            # one last check
            print(f"Relic to add: {rupdate_key}")
            relic = reg.relics[rupdate_key]
            edb = cursor.execute("""select * from relic
                where era = ? and minor = ?""",
                (relic.era, relic.minor_name)).fetchall()
            if len(edb) >= 1:
                print(edb)
                connection.rollback()
                raise Exception("There's a `new` relic that already exists?")
            else:
                cursor.execute(
                    "insert into relic values (?, ?, ?);",
                    (relic.era, relic.minor_name, relic.vaulted)
                )
        for vupdate_tuple in updates["relic"]["vaulting"]:
            (relic_key, old_vaulted, new_vaulted) = vupdate_tuple
            print(f"Updating vaulted status for {relic_key} to {new_vaulted}")
            relic = reg.relics[relic_key]
            edb = cursor.execute("""select * from relic
                where era = ? and minor = ?""",
                (relic.era, relic.minor_name)).fetchall()
            if len(edb) != 1:
                print(edb)
                connection.rollback()
                raise Exception("Want to update vaulted status " +
                "but wrong number of entries exists?")
            elif edb[0][2] != old_vaulted:
                print(edb)
                print(f"{relic.era} {relic.minor}: {new_vaulted}")
                connection.rollback()
                raise Exception("Want to update vaulted status " +
                "but script has wrong `old vaulted` status?")
            else:
                cursor.execute(
                    """update relic set vaulted = ?
                    where era = ? and minor = ?""",
                (relic.era, relic.minor_name, new_vaulted))
        for pupdate_key in updates["prime"]["new"]:
            # primes don't depend on anything either
            print(f"Prime to add: {pupdate_key}")
            edb = cursor.execute("""select * from prime
                where name = ?""",
                (pupdate_key,)).fetchall()
            if len(edb) > 0:
                print(edb)
                connection.rollback()
                raise Exception("Want to update primes in db " +
                "but db already has entry(ies?) for that prime?")
            else:
                cursor.execute(
                    """insert into prime values(?, NULL)""",
                    (pupdate_key,)
                )
        for aupdate_key in updates["part"]["new"]:
            print(f"Prime part to add: {aupdate_key}")
            # prime parts depend on primes, which we did above
            part_obj = reg.parts[aupdate_key]
            prime_base = part_obj.prime_obj.name
            part_role = part_obj.role
            edb = cursor.execute("""select * from part
                where base = ? and role = ?""",
                (prime_base, part_role) ).fetchall()
            if len(edb) > 0:
                print(edb)
                connection.rollback()
                raise Exception("Want to update parts in db " +
                "but db already has entry(ies?) for that part?")
            else:
                cursor.execute(
                    """insert into part values (?, ?)""",
                    (prime_base, part_role)
                )
        for rupdate_tuple in updates["reward"]["new"]:
            print(f"Full reward string to update: {rupdate_tuple}")
            # I'm not even going to try and unpack the tuple
            # It's pretty much guaranteed to be in the correct format from above.
            # rewards depend on relics and primes.
            # we did both above.
            # the end is in sight.
            edb = cursor.execute(
                """select * from reward where
                    era = ? and
                    minor = ? and
                    base = ? and
                    role = ? and
                    rarity = ?""",
                rupdate_tuple
            ).fetchall()
            if len(edb) > 0:
                print(edb)
                connection.rollback()
                raise Exception("Want to add a new reward " +
                "but db already has this exact reward...")
            else:
                cursor.execute(
                    """insert into reward values (?, ?, ?, ?, ?)""",
                    rupdate_tuple
                )