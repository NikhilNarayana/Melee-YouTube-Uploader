# Melee-YouTube-Uploader
A YouTube Uploader for my Melee recordings

A modified version of FRC-YouTube-Uploader for Super Smash Bros. Melee.

## To Do
* Automate creation of thumbnails
* Automate file picking
* Update this README even more

## Contributing
PRs are appreciated and will be reviewed quickly, the only code quality standard I have is to follow PEP8 standard except for the line length. If you have trouble understanding my code just ask me.

## Current Feature Set:
* Upload videos
* Queue and dequeue Videos to upload
* Adds a lot of relevant tags
* Adds to a YouTube playlist
* Saves and loads form values
* Loading values from history

## How to Setup
1. Install [Python 3.7.1](https://www.python.org/downloads/release/python-371/) for your OS with the PATH added and make sure there are no other versions of Python 3.
2. Install the program with `pip3 install -U meleeuploader`. If you want untested features you can download the repo and install with `pip3 install -U /path/to/repo`
3. Start the program by running `meleeuploader` in terminal.
4. Add in the necessary info in the Event Values and Match Values tabs
5. Hit submit every time a match finishes.
6. Update forms with the next match's info.
7. Enjoy not having to deal with YouTube's front end 🎉.

### Create Your Own Credentials
In the future I will not be including YouTube API credentials with this project. So here is a guide to create your own credentials.

1. Open the [Google Developer Console](https://console.developers.google.com/)
2. Hit the `Select Project` button near the top and create a new project.
3. Once the project is created, select the project.
4. Hit the `Enable APIs and Services` button and enable the YouTube Data API V3.
5. Once the API is enabled it will tell you to create credentials and there will be a button to press.
6. Follow the steps laid out in the credential creation wizard and make sure to select `Other UI` for `Where will you be calling the API from?` and `User Data` for `What data will you be accessing?`.
7. Once you have downloaded your credentails remember to rename them `client_secrets.json` (if you don't see the `.json` when renaming the file just use `client_secrets`) and put the file in `C:\Users\[Your Username]\` or, if you are on macOS or Unix, whatever `echo ~` returns in terminal. macOS users can also just do `open ~` to open a Finder window at that directory.

### Additional Setup Options
#### Windows
If you want to launch the application easily, you can find the exe by hitting the Windows key and typing `meleeuploader`, if that doesn't show the option to run the command then you can probably find the exe at `C:\Users\[Your Username]\AppData\Local\Programs\Python\Python37\Scripts\`. Pinning the exe to the taskbar allows quick access to the program.

#### Mac and Unix
`meleeuploader &` if you want to hide the terminal window. There are probably ways to launch the program quicker, but I don't use macOS/Unix for uploading usually.

## How to use advanced features

### History - Fixing an upload that didn't work
History was built so I could fix uploads that exceeded the title limit on YouTube (100 characters). 

By loading the history window from the menubar, you can double click any row in the list to reload the form with the values you inputted for that submission. Every submission will create a new entry, but the GUI is only updated on load, you will need to close and reopen it to see new entries.

### Queue - Saving uploads for later
Queue was built so I could upload VODs after an event because the venue didn't have the bandwidth to support streaming and uploading simultaneously. 

Queue refers to the list of upcoming uploads in the status tab. By selecting `Toggle Queue` you can toggle the queue from uploading videos, but continue to allow the queue to receive entries. Once you have finished adding all the VODs you want to upload, selecting `Save Queue` will write the entire queue to your disk to be loaded later on. Finally, using `Load Queue` will load the entire queue file and start uploading immediately.
