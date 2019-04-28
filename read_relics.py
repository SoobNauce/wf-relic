#! /usr/bin/env python3

# Each relic has 6 "prime parts" as a reward

# Each part has any number of relics that reward it.
# Each part belongs to one prime.

# Each prime has a certain number of parts.

# The rest is unique data such as relic tier and vaultedness.

source_table = "from_wiki_20190403.txt"

debug = False

def debug_msg(*args, **kwargs):
    if debug:
        print(*args,**kwargs)

class Relic:
    def __init__(self, name, vaulted = 0):
        self.name = name# Axi S2
        (self.era, self.minor_name) = name.split(" ")
        self.rewards = {
            "Common": set(),# Akbolto Prime Barrel
            "Uncommon": set(),# Forma Blueprint (etc)
            "Rare": set()
        }
        self.vaulted = vaulted# 0/1/2
    
    def register_reward(self, reward_obj, rarity):
        self.rewards[rarity].add(reward_obj)# Akbolto Prime Barrel, common
    
    def serialize_helper(self):
        name = self.name
        vaulted = self.vaulted
        commons = [
            r.full_name() for r in self.rewards["Common"]
        ]
        uncommons = [
            r.full_name() for r in self.rewards["Uncommon"]
        ]
        rares = [
            r.full_name() for r in self.rewards["Rare"]# there should be only one
        ]
        return name, vaulted, commons, uncommons, rares
    def full_serialize(self):
        (n, v, c, u, r) = self.serialize_helper()
        c_s = ", ".join(c)
        u_s = ", ".join(u)
        r_s = ", ".join(r)
        return (
            "{{name: {}, vaulted: {}, " +
            "Common: [{}], Uncommon: [{}], Rare: [{}]}}"
        ).format(n, v, c_s, u_s, r_s)

    def pretty_print(self):
        (n, v, c, u, r) = self.serialize_helper()
        c_s = "\n\t\t".join(c)
        u_s = "\n\t\t".join(u)
        r_s = "\n\t\t".join(r)
        return ("{name}: {vaulted}\n\t" +
            "Common: {commons}\n\t" +
            "Uncommon: {uncommons}\n\t" +
            "Rares: {rares}").format(
            name=n,
            vaulted=["False", "True", "Baro"][v],
            commons=c_s,
            uncommons=u_s,
            rares=r_s
        )

class Prime:
    def __init__(self, name):
        self.name = name
        self.parts = {}
    def register_part(self, part):
        self.parts[part.full_name()] = part
    
class Part:
    def __init__(self, role, prime_obj):
        # always create prime object before part
        self.role = role# str
        self.prime_obj = prime_obj
        self.relics = {}# "Lith G1" -> "([lith_g1_object], common)"
    def register_relic(self, relic, rarity):
        self.relics[relic.name] = (relic, rarity)
    def full_name(self):
        return self.prime_obj.name + " " + self.role

class Registry:
    def __init__(self):
        self.relics = {}# "Lith G2" -> ((lith g2 relic object))
        self.primes = {}# "Mirage Prime" -> ((prime object))
        self.parts = {}# "Mirage Prime Chassis" -> ((prime part object))
    def register_reward(self, prime_s, part_s, relic_s, rarity, vaulted):
        """For sanity: only inputs strings, not objects."""
        full_part_s = prime_s + " " + part_s# for indexing only

        if relic_s not in self.relics:
            relic = Relic(relic_s, vaulted)
            self.relics[relic_s] = relic
        else:
            relic = self.relics[relic_s]
        
        if prime_s not in self.primes:
            prime = Prime(prime_s)
            self.primes[prime_s] = prime
        else:
            prime = self.primes[prime_s]
        
        if full_part_s not in self.parts:
            part = Part(
                part_s,
                prime
            )
            self.parts[full_part_s] = part
        else:
            part = self.parts[full_part_s]
        
        prime.register_part(part)# don't need rarity for prime parts
        relic.register_reward(part, rarity)
        part.register_relic(relic, rarity)

        
def parse_line(line):
    prime_s = None
    part_s = None
    rs = None
    lsp = line.strip().split(" \t")
    # Line length detection
    if len(lsp) == 0:# empty line
        debug_msg("[{}]".format(line))
        debug_msg("empty line, skipping.\n")
        return None
    elif len(lsp) == 1:# just a relic or a malformed line
        rs = lsp[0].split(" ")# rs = relic description string
        # i.e. "neo v1 uncommon (v)" or something like that
        if len(rs) < 3:# image
            debug_msg("[{}]".format(line))
            debug_msg("image detected, skipping\n")
            return None
    elif len(lsp) == 2:# Blueprint \tLith H1 Common (V)
        rs = lsp[1].split(" ")
        part_s = lsp[0]
    elif len(lsp) == 3:# $prime, $part, $relic_info
        (prime_s, part_s, pre_rs) = lsp
        rs = pre_rs.split(" ")
    else:# "I don't understand this line. Can I ignore it?"
        print("malformed line, returning early")
        return line
    
    # Unpack relic reward info
    if len(rs) < 3 or len(rs) > 4:
        print("malformed reward line (wrong size)")
        print("line {}".format(rs))
        return line
    if len(rs) == 3:# "neo v1 uncommon"
        vaulted = 0
    elif len(rs) == 4:# "neo v1 uncommon (V)" or "(B)"
        vs = rs[-1]
        if vs == "(V)": vaulted = 1
        elif vs == "(B)": vaulted = 2
        else:
            print("unknown vaulted status {}".format(vs))
            return line
    rarity = rs[2]
    relic_s = " ".join(rs[:2])

    # prime_s can be None
    # part_s can be None
    # relic_s, rarity, and vaulted should Always exist.
    if relic_s == None or rarity == None or vaulted == None:
        print("malformed line. Something didn't trigger.")
        return line
    
    return (prime_s, part_s, relic_s, rarity, vaulted)

def read_relics(input_file):
    x = []
    with open(input_file) as infile:
        x = infile.read().split("\n")
    reward_registry = Registry()
    prime_s = None
    part_s = None
    # prime_s and part_s are the only things that can be missing from a line
    for line in x:
        parsed = parse_line(line)
        # Unpacking time
        # Error conditions
        if type(parsed) == str:
            print("Unrecoverable parser error. See log.")
            raise ValueError("Unrecoverable parser error\nLine: {}".format(line))
        elif parsed == None:
            debug_msg("No log data found, line can be skipped.")
            continue
        # prime_s, part_s, relic_s, rarity, vaulted
        if parsed[0] != None:# Normal for a line to not include a prime
            prime_s = parsed[0]
        if parsed[1] != None:# Normal for it not to include a part
            part_s = parsed[1]
        
        relic_s = parsed[2]
        rarity = parsed[3]
        vaulted = parsed[4]
        
        reward_registry.register_reward(
            prime_s, part_s, relic_s, rarity, vaulted
        )
    return reward_registry

if __name__ == "__main__":
    import random
    master_registry = mr = read_relics(source_table)

    relic_objs = master_registry.relics
    relic_names = list(relic_objs.keys())
    prime_objs = master_registry.primes
    prime_names = list(prime_objs.keys())
    part_objs = master_registry.parts
    part_names = list(part_objs.keys())

    # Sanity check relic listing


    random.shuffle(relic_names)
    for n in relic_names:
        print("Checking relic `{}`: ".format(n), end="")
        nr = relic_objs[n]
        print("Era, minor are {} / {}, ".format(
            nr.era, nr.minor_name
        ), end="")
        if (
            (len(nr.rewards["Common"]) != 3) or
            (len(nr.rewards["Uncommon"]) != 2) or
            (len(nr.rewards["Rare"]) != 1)
        ):
            print("Not enough rewards in relic?")
            print(nr.pretty_print())
            input(">>> ")
        else: 
            print("rewards are fine (3/2/1), ", end="")
        if(nr.name != n):
            print("Relic wasn't registered under correct name?")
            print("relic.name: {}".format(nr.name))
            input(">>> ")
        else:
            print("name matches, ", end="")
        if(nr.vaulted not in [0, 1, 2]):
            print("Relic does not correctly identify vaulted status?")
            print("status: {}".format(nr.vaulted))
            input(">>> ")
        else:
            print("{} which is fine, ".format(
                ["Unvaulted", "Vaulted", "Baro-only"][nr.vaulted]
            ), end="")
        print("Seems fine.")
        
    # Sanity check prime part listing
    random.shuffle(part_names)

    for n in part_names:
        print("Checking part `{}`: ".format(n), end="")
        np = part_objs[n]
        
        if len(np.relics.keys()) == 0:
            print("Part has no relics that reward it?")
            input(">>> ")
        else:
            print("Rewarded by {} relic(s), ".format(
                len(np.relics.keys())),
                end="")
        print("role is `{}`, ".format(np.role), end="")
        base = np.prime_obj
        print("base prime is `{}`, ".format(base.name), end="")
        if base.name not in mr.primes.keys():
            print("Couldn't find that prime in master registry.")
            input(">>> ")
        else:
            print("which is in the registry, ", end="")
        print("says its full name is `{}`, ".format(
            np.full_name()), end="")
        print("Seems fine.")
    
    # Sanity check prime listing
    random.shuffle(prime_names)

    for n in prime_names:
        print("Checking prime `{}`: ".format(n), end="")

        print("Seems fine.")