# Melee-YouTube-Uploader
A YouTube Uploader for my Melee recordings

A modified version of FRC-YouTube-Uploader for Super Smash Bros. Melee and Super Smash Bros. Ultimate.

Already public/non-sensitive data is collected on Google Sheets [here](https://docs.google.com/spreadsheets/d/1TavrlG3uiLLJUwrx6UB0CCyjbiWElYE8sCev6fWclaw/edit#gid=0), this is to help figure out if certain highly specific features are being used.


**IMPORTANT NOTE**

This application **DOES NOT** support enabling monetization at the moment. I highly suggest you upload videos as unlisted and set monetization settings before making them public or monitor your uploads and update monetization settings as they are uploaded (you can adjust the settings while the files are being uploaded without breaking anything). If you see the YouTube ContentID API in your Google Developer Console and are willing to help me test updates to fix the issue DM me on twitter at @xMetonym.

## To Do
* Automate creation of thumbnails
* Maybe other stuff

## Known Issues
* Fails to work when antivirus software is installed, maybe

## Contributing
PRs are appreciated and will be reviewed quickly, the only code quality standard I have is to follow PEP8 standard except for the line length. If you have trouble understanding my code just ask me.

## Questions and Support
I am always open to help setup the program or fix any techincal issues you may have. Please send me a DM on twitter with your issue and I'll get you sorted out.

## Current Feature Set:
* Upload videos
* Manual or automatic file selection
* Queue and dequeue Videos to upload
* Add many relevant YouTube tags
* Add to a YouTube playlist
* Save and load form values
* Load old submissions from history
* Save a queue to be uploaded later
* Melee and Ultimate Character Lists
* Hook into Scoreboard Assistant, Stream Control<sup>*</sup>, OBS
* Automatic Updates

<sup>*</sup>you must adjust your configuration to use specific key names listed [here](https://github.com/NikhilNarayana/Melee-YouTube-Uploader/releases/tag/v1.10)

## How to Setup - Video Version: https://youtu.be/zrcf4t_qk5A
1. Install [Python 3.7.2](https://www.python.org/downloads/release/python-372/) for your OS with the PATH added and make sure there are no other versions of Python 3.
2. Install the program by typing `pip3 install -U meleeuploader` into Command Prompt/Terminal. If you want untested features you can download the repo and install with `pip3 install -U /path/to/repo`
3. Start the program by running `meleeuploader` for the Melee character list or `smashuploader` for the Ultimate character list in Command Prompt/Terminal.
4. Select the YouTube profile you would like to use for the first authentication request and then any google account for the second authentication request. If the second one fails, close your web browser and then run the command to open the program again.
5. Add in the necessary info in the Event Values and Match Values tabs
6. Hit submit when the match finishes.
7. Update forms with the next match's info.
8. Repeat steps 5-7 and enjoy not having to deal with YouTube's front end 🎉.

### Create Your Own Credentials
In the future I will not be including YouTube API credentials with this project. So here is a guide to create your own credentials.

1. Open the [Google Developer Console](https://console.developers.google.com/)
2. Hit the `Select Project` button near the top and create a new project.
3. Once the project is created, select the project.
4. Hit the `Enable APIs and Services` button and enable the YouTube Data API V3 and the Google Sheets API.
5. Once the APIs are enabled it will tell you to create credentials and there will be a button to press.
6. Follow the steps laid out in the credential creation wizard and make sure to select `Other UI` for `Where will you be calling the API from?` and `User Data` for `What data will you be accessing?`.
7. Once you have downloaded your credentails remember to rename them `client_secrets.json` (if you don't see the `.json` when renaming the file just use `client_secrets`) and put the file in `C:\Users\[Your Username]\` or, if you are on macOS or Unix, whatever `echo ~` returns in terminal. macOS users can also just do `open ~` to open a Finder window at that directory.
8. If you already created YouTube Account credentials for the program, open the program and select `Settings -> Remove YouTube Credentials`

### Additional Setup Options
#### Windows
If you want to launch the application easily, you can find the exe by hitting the Windows key and typing `meleeuploader`, if that doesn't show the option to run the command then you can probably find the exe at `C:\Users\[Your Username]\AppData\Local\Programs\Python\Python37\Scripts\`. Pinning the exe to the taskbar allows quick access to the program.

If you would like to have no console window on your screen, you will need to find out where your pythonw.exe file is (it should be in the same place your python.exe) and create a shortcut to it. Then open the shortcut properties window and edit the target to include `-m meleeuploader` for melee or `-m meleeuploader ult` for ultimate at the end. This can then be pinned to your taskbar for easy access. This method does not allow authenticating yourself so you will have to fall back to CMD/Terminal for that part.

#### Mac and Unix
`meleeuploader &` if you want to hide the terminal window. There are probably ways to launch the program quicker, but I don't use macOS/Unix for uploading usually.

## How to use each field
### Required
`Event Name`, `Title Format`, `Video Privacy`, `File`, `Match Type`, and `Player Tags` are the only required fields for uploading any file.

#### File
File is able to be used as either a file or directory input. Because of how the input selector is setup you will need to select a file within the directory you wish to use and then you can delete the filename from the field. If you select a directory it will not be deleted after submission.

When using this quirk of the field, it will find the newest file in the directory you give it, so make sure no other files are written to this folder other than the recordings. This is best used for uploading or queueing videos during an event.

#### Title Format 
All the options support no characters and the available options can be expanded upon on request.

### Optional
#### Match Type Prefix and Suffix
These are fairly self explanatory, you can add a bit of text before and after the `Match Type`. When submitting the video the `Prefix` is kept while the `Suffix` is cleared.

#### Sponsor Tag
This field will be added to the player tag like so `{sponsor} | {player}` resulting in names like `TSM | Leffen`.

#### Characters
Melee characters are currently ordered by tier list placing, according to the 2015 official NTSC tier list.  
Ultimate characters are currently ordered by the default character select screen without echo stacking.  
If you don't add any characters for either player, both players will not have characters in the title.  
Characters that are selected will be in the order they are shown in the list, not the selected order (unfortunate issue with the GUI framework).  
You can swap the character list using the menu bar or load the preferred character list by using `meleeuploader` for Melee and `smashuploader` for Ultimate.  
There is also the option to load your own character list, instructions can be found at the bottom.

#### YouTube PlaylistID
The URL of the playlist after creation can be put here, the program will trim it to just the part it needs. The URL should look like `https://www.youtube.com/playlist?list=PLSCJwgNAP2cXdlHlwbZr38JDHuuc8vx_s`, if the address has a string with `PL` at the start, it should work.

#### Bracket Link
Any URL will work here, just make sure to include `https://` so YouTube users can click on the link in the description.

#### Tags
If you want to add additional tags, for a specific event or your channel, add them here. Separate the tags with commas and don't worry about leading or trailing spaces.  
Also multiple tags about Melee and the players are added by the program so don't add any related to those in this field.

#### Description
Additional text can be added to the description here, it will go between the bracket link and the credit text. If you would like to put the bracket link in a different spot, don't input anything in `Bracket Link` and instead insert your format in `Description`.

#### Submit
The submit button does a lot, it adds submission to queue, clears fields in match values that aren't generally needed for consecutive matches, and prevents you from adding submissions that don't meet the minimum criteria.

## How to use advanced features - Video Version: https://youtu.be/mw0sP7YJVfE

### History - Fixing an upload that didn't work
History was built so I could fix uploads that exceeded the title limit on YouTube (100 characters). 

By loading the history window from the menubar, you can double click any row in the list to reload the form with the values you inputted for that submission. Every submission will create a new entry, but the history window is only updated on load, you will need to close and reopen it to see new entries.

### Queue - Saving uploads for later
Queue was built so I could upload VODs after an event because the venue didn't have the bandwidth to support streaming and uploading simultaneously. 

Queue refers to the list of upcoming uploads in the status tab. By selecting `Toggle Uploads` you can toggle the uploading function, but continue to add entries to the queue. Once you have finished adding all the VODs you want to upload, selecting `Save Queue` will write the entire queue to your disk to be loaded later on. Finally, using `Load Queue` will load the entire queue file and start uploading immediately.

### Scoreboard Assistant Websocket - Never retype anything
SA Websocket was built so I could avoid retyping information that I put into Scoreboard Assistant.

To enable the websocket open the `Settings` menu tab and select the `Enable Websocket` option. Just make sure that SA is open before you start the websocket.

The program will pull from the `Player 1`, `Player 2`, and `Match` fields. The `Match` field will be parsed to find which of the match types defined in the program are a substring, then it will split the input at the substring and update `Match Prefix` and `Match Suffix` with whatever is left over. For example, `Doubles - Winners R1` as the input would result in `Doubles -` and `R1` being the prefix and suffix respectively.

There is also support for character selection if you use stock icons from this [link](https://drive.google.com/file/d/1L8M-4FUDcQo-2cuh1Ak_VabJSQlWz8B_/view?usp=sharing).

### OBS Websocket - Never submit manually
This is a peculiar feature that I built with only myself in mind. There are no plans to expand what I've set it up to do.

I've set it up so once recording has been stopped, the application will submit the information that is currently inputted. This combined with `SA Websocket` is a powerful feature set to quickly queue sets. The only info that will have to be set if using that combo is the `Characters` for both players or you could just ignore those and automate the whole uploading procedure from start to finish.

In addition to enabling the settings you will need to update OBS with the websocket plugin found here: https://github.com/Palakis/obs-websocket

### Custom Character List
You can add your own custom character lists by putting comma separated names in a file called `.smash_custom_list.txt` in your root directory.  
If you don't know where your root directory is, open the program and select `Characters -> Custom` and the program will make a blank text file where it is supposed to be.
