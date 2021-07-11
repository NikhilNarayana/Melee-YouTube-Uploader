#!/usr/bin/env python3

import os
import pkg_resources

__version__ = pkg_resources.require("MeleeUploader")[0].version

firstrun = True
stop_thread = False
melee = True
game = "melee"
custom = False
stopUpdates = False
submitted = True
startQueue = False
saveOnSubmit = False

youtube = None
sheets = None
partner = None
loadedQueue = False

root = os.path.expanduser("~")
smash_folder = os.path.join(root, ".smashuploader")
os.makedirs(smash_folder, exist_ok=True)

form_values = os.path.join(root, '.smash_form_values.json')
queue_values = os.path.join(root, ".smash_queue_values.txt")
log_file = os.path.join(root, ".smash_log.txt")
custom_list_file = os.path.join(root, ".smash_custom_list.txt")
youtube_file = os.path.join(root, ".smash-oauth2-youtube.json")
partner_file = os.path.join(root, ".smash-oauth2-partner.json")

abbrv = "smash"
short_name = "meleeuploader"
long_name = "Melee YouTube Uploader"

rowRange = "Data!A1:G1"

credit = "Uploaded with Melee-YouTube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"

melee_tags = ("Melee", "Super Smash Brothers Melee", "Smash Brothers",
              "Super Smash Bros. Melee", "meleeuploader", "smashuploader" "SSBM", "ssbm")
ult_tags = ("Ultimate", "Super Smash Brothers Ultimate", "Smash Brothers",
            "Super Smash Bros. Ultimate", "smashuploader", "SSBU", "ssbu")
s64_tags = ("Smash 64", "64", "Super Smash Brothers", "Super Smash Bros.", "s64",
            "Smash Brothers", "smashuploader", "SSB", "SSB64", "ssb", "ssb64")
rivals_tags = ("Rivals of Aether", "RoA", "roa", "Rivals", "smashuploader")
splatoon2_tags = ("Splatoon 2", "Splat 2", "smashuploader")
tags = melee_tags

minchars = {
    'Jigglypuff': "Puff",
    'Captain Falcon': "C. Falcon",
    'C. Falcon': "Falcon",
    'Ice Climbers': "Icies",
    'Pikachu': "Pika",
    'Doctor Mario': "Dr. Mario",
    'Dr. Mario': "Doc",
    'Ganondorf': "Ganon",
    'Young Link': "YLink",
    'Donkey Kong': "DK",
    'Mr. Game & Watch': "G&W",
    'Mewtwo': "Mew2",
    'Dark Samus': "D. Samus",
    'Meta Knight': "MK",
    'Dark Pit': "D. Pit",
    'Zero Suit Samus': "ZSS",
    'Pokemon Trainer': "PK Trainer",
    'Diddy Kong': "Diddy",
    'King Dedede': "DDD",
    'Toon Link': "TLink",
    'Wii Fit Trainer': "Wii Fit",
    'Rosalina & Luma': "Rosa",
    'Mii Fighter': "Mii",
    'Bayonetta': "Bayo",
    'King K. Rool': "K. Rool",
    'Piranha Plant': "Plant",
    'Banjo & Kazooie': "Banjo",
    'Terry Bogard': "Terry",
}

ult_chars = ('Mario', 'Donkey Kong', 'Link', 'Samus', 'Dark Samus', 'Yoshi',
             'Kirby', 'Fox', 'Pikachu', 'Luigi', 'Ness', 'Captain Falcon',
             'Jigglypuff', 'Peach', 'Daisy', 'Bowser', 'Ice Climbers', 'Sheik',
             'Zelda', 'Dr. Mario', 'Pichu', 'Falco', 'Marth', 'Lucina',
             'Young Link', 'Ganondorf', 'Mewtwo', 'Roy', 'Chrom',
             'Mr. Game & Watch', 'Meta Knight', 'Pit', 'Dark Pit',
             'Zero Suit Samus', 'Wario', 'Snake', 'Ike', 'Pokemon Trainer',
             'Squirtle', 'Ivysaur', 'Charizard', 'Diddy Kong', 'Lucas',
             'Sonic', 'King Dedede', 'Olimar', 'Lucario', 'R.O.B', 'Toon Link',
             'Wolf', 'Villager', 'Mega Man', 'Wii Fit Trainer',
             'Rosalina & Luma', 'Little Mac', 'Greninja', 'Mii Brawler',
             'Mii Gunner', 'Mii Swordfighter', 'Palutena', 'Pac-Man', 'Robin',
             'Shulk', 'Bowser Jr.', 'Duck Hunt', 'Ryu', 'Ken', 'Cloud',
             'Corrin', 'Bayonetta', 'Inkling', 'Ridley', 'Simon', 'Richter',
             'King K. Rool', 'Isabelle', 'Incineroar', 'Piranha Plant',
             'Joker', 'Hero', 'Banjo & Kazooie', 'Terry Bogard', 'Byleth',
             'Min Min', 'Steve', 'Sephiroth', 'Pyra', 'Mythra', 'Kazuya')

melee_chars = ('Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach',
               'Captain Falcon', 'Ice Climbers', 'Pikachu', 'Samus',
               'Dr. Mario', 'Yoshi', 'Luigi', 'Ganondorf', 'Mario',
               'Young Link', 'Donkey Kong', 'Link', 'Mr. Game & Watch',
               'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser', 'Kirby')

s64_chars = ('Pikachu', 'Kirby', 'Captain Falcon', 'Fox', 'Yoshi', 'Jigglypuff',
             'Mario', 'Samus', 'Donkey Kong', 'Ness', 'Link', 'Luigi')

rivals_chars = ('Zetterburn', 'Orcane', 'Wrastor', 'Kragg', 'Forsburn', 'Maypul',
                'Absa', 'Etalus', 'Ranno', 'Clairen', 'Sylvanos', 'Elliana',
                'Ori and Sein', 'Shovel Knight',)

splatoon2_chars = ()

min_match_types = {
    "Round ": "R",
    "Round Robin": "RR",
    "Winners Finals": "WF",
    "Losers Finals": "LF",
    "Grand Finals": "GF",
    "Money Match": "MM",
    "Crew Battle": "Crews",
    "Semifinals": "Semis",
    "Quarterfinals": "Quarters",
    "Semis": "SF",
    "Quarters": "QF"
}

titleformat = (("Event - Round - P1 (Fox) vs P2 (Fox)", "{ename} - {round} - {p1} ({p1char}) vs {p2} ({p2char})"),
               ("Event - P1 (Fox) vs P2 (Fox) - Round", "{ename} - {p1} ({p1char}) vs {p2} ({p2char}) - {round}"),
               ("Event - Round - (Fox) P1 vs P2 (Fox)", "{ename} - {round} - ({p1char}) {p1} vs {p2} ({p2char})"),
               ("Round - P1 (Fox) vs P2 (Fox) - Event", "{round} - {p1} ({p1char}) vs {p2} ({p2char}) - {ename}"),
               ("P1 (Fox) vs P2 (Fox) - Round - Event", "{p1} ({p1char}) vs {p2} ({p2char}) - {round} - {ename}"))

titleformat_min = {
    "{ename} - {round} - {p1} ({p1char}) vs {p2} ({p2char})": "{ename} - {round} - {p1} vs {p2}",
    "{ename} - {p1} ({p1char}) vs {p2} ({p2char}) - {round}": "{ename} - {p1} vs {p2} - {round}",
    "{ename} - {round} - ({p1char}) {p1} vs {p2} ({p2char})": "{ename} - {round} - {p1} vs {p2}",
    "{round} - {p1} ({p1char}) vs {p2} ({p2char}) - {ename}": "{round} - {p1} vs {p2} - {ename}",
    "{p1} ({p1char}) vs {p2} ({p2char}) - {round} - {ename}": "{p1} vs {p2} - {round} - {ename}"
}

match_types = ("Pools", "Round Robin", "Finals", "Winners", "Losers", "Winners Finals",
               "Losers Finals", "Grand Finals", "Money Match", "Crew Battle",
               "Ladder", "Friendlies", "Thug Finals")
