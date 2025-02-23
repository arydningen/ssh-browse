### Changelog

#### v0.0.1 - v0.5.0
**New Features:**
- Basic functionality.

**Notes:**
- Very usable basic ssh-browser utility.
- Using ssh-browse with tmux can be extremely powerful.

#### v0.5.0
**New Features:**
- Added help window.
- Added color themes.
- Improved footer.

**Known Bugs:**
- `BUG-001`: Crash when list of hosts is longer than screen size.

**Notes:**
- Refactored code to be more modular.

#### v0.5.2
**Notes**
- First published version.
- It's a cleaned up version of v0.5.0

#### v0.5.3
**New Features:**
- Configurable notes location. `notes_dir` can be set in `config.json`
- Ping marked hosts.
- Nice pinging feedback.
- Notes preview

**Bug Fixes:**
- `BUG-001`: Crash when list of hosts is longer than screen.

#### v0.5.4

**Changes:**
- Modified keybindings.

#### v0.5.5
**New Features:**
- Search function

#### v0.5.6
**Changes:**
- Ping all now just pings visible hosts.

#### v0.5.7
**Bug Fixes:**
- Fixed bug! Program crashed if category list exceeded bounds.

**Changes:**
- Impoved column size calculations.
- Pressing ESC while searchpanel is visible closes it and clears the searchfilter.
- Searchfilter now also applies to hostname value.

**New Features:**
- Can import hosts from JSON file.
- Scrolling categories.