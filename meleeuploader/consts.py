#!/usr/bin/env python3

import os
import pkg_resources

__version__ = pkg_resources.require("MeleeUploader")[0].version

firstrun = True
stop_thread = False
melee = True
custom = False
youtube = None
sheets = None
partner = None
loadedQueue = False

form_values = os.path.join(os.path.expanduser("~"), '.smash_form_values.json')
queue_values = os.path.join(os.path.expanduser("~"), ".smash_queue_values.txt")
log_file = os.path.join(os.path.expanduser("~"), ".smash_log.txt")
custom_list_file = os.path.join(os.path.expanduser("~"), ".smash_custom_list.txt")

abbrv = "smash"
short_name = "meleeuploader"
long_name = "Melee YouTube Uploader"

spreadsheetID = "1TavrlG3uiLLJUwrx6UB0CCyjbiWElYE8sCev6fWclaw"
rowRange = "Data!A1:G1"

credit = "Uploaded with Melee-YouTube-Uploader (https://github.com/NikhilNarayana/Melee-YouTube-Uploader) by Nikhil Narayana"


melee_tags = ("Melee", "Super Smash Brothers Melee", "Smash Brothers",
              "Super Smash Bros. Melee", "meleeuploader", "SSBM", "ssbm")
ult_tags = ("Ultimate", "Super Smash Brothers Ultimate", "Smash Brothers",
            "Super Smash Bros. Ultimate", "smashuploader", "SSBU", "ssbu")

minchars = {
    'Jigglypuff': "Puff",
    'Captain Falcon': "Falcon",
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
             'Joker')

melee_chars = ('Fox', 'Falco', 'Marth', 'Sheik', 'Jigglypuff', 'Peach',
               'Captain Falcon', 'Ice Climbers', 'Pikachu', 'Samus',
               'Dr. Mario', 'Yoshi', 'Luigi', 'Ganondorf', 'Mario',
               'Young Link', 'Donkey Kong', 'Link', 'Mr. Game & Watch',
               'Mewtwo', 'Roy', 'Zelda', 'Ness', 'Pichu', 'Bowser', 'Kirby')

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
               ("Round - P1 (Fox) vs P2 (Fox) - Event", "{round} - {p1} ({p1char}) vs {p2} ({p2char}) - {ename}"),)

titleformat_min = {
    "{ename} - {round} - {p1} ({p1char}) vs {p2} ({p2char})": "{ename} - {round} - {p1} vs {p2}",
    "{ename} - {p1} ({p1char}) vs {p2} ({p2char}) - {round}": "{ename} - {p1} vs {p2} - {round}",
    "{ename} - {round} - ({p1char}) {p1} vs {p2} ({p2char})": "{ename} - {round} - {p1} vs {p2}",
    "{round} - {p1} ({p1char}) vs {p2} ({p2char}) - {ename}": "{round} - {p1} vs {p2} - {ename}"
}

match_types = ("Pools", "Round Robin", "Winners", "Losers", "Winners Finals",
               "Losers Finals", "Grand Finals", "Money Match", "Crew Battle",
               "Ladder", "Friendlies")
