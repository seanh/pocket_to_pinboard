Pocket to Pinboard Sync
=======================

Syncs bookmarks from Pocket to Pinboard.

Usage
-----

```console
$ python -m venv .venv
$ .venv/bin/pip install -r requirements.txt
$ POCKET_CONSUMER_KEY=$YOUR_POCKET_CONSUMER_KEY POCKET_ACCESS_TOKEN=$YOUR_POCKET_ACCESS_TOKEN PINBOARD_AUTH_TOKEN=$YOUR_PINBOARD_AUTH_TOKEN .venv/bin/python pocket_to_pinboard.py
```

To get a Pocket consumer key and access token follow Pocket's instructions: https://getpocket.com/developer/docs/authentication.
This blog post is also helpful: https://www.jamesfmackenzie.com/getting-started-with-the-pocket-developer-api/.

To get a Pinboard API token go to: https://pinboard.in/settings/password.

Features
--------

* Syncs all your bookmarks from Pocket to Pinboard, starting with the oldest
* You can kill it at any time and if you run it again it'll pick up where it left off
* Once it's finished syncing all your bookmarks, run it again and it'll sync any new bookmarks that've been saved to Pocket since
* All bookmarks created in Pinboard will have the `via:pocket` tag
* Timestamps of bookmarks created in Pinboard will match the timestamps when they were added to Pocket
* Also syncs a bookmark's tags from Pocket to Pinboard
  * Pocket tags can contain spaces, Pinboard tags can't. Any spaces in your Pocket tags will be replaced with underscores
* Stays well within Pocket and Pinboard's API limits, even when syncing a lot of bookmarks
* Run it periodically on GitHub Actions

Limitations
-----------

* Only syncs from Pocket to Pinboard, not the other way round. Any changes to bookmarks in Pinboard won't be synced to Pocket
* Bookmarks that already exist in Pinboard won't be updated:
  * If you manually save a bookmark in both Pinboard and Pocket the script won't update that bookmark in Pinboard. For example any tags from Pocket won't be synced
  * If you run the script and it syncs a bookmark to Pinboard, then you edit the bookmark in Pocket (e.g. changing its tags) and run the script again, the bookmark won't be re-synced
* Bookmarks deleted from Pocket won't be deleted from Pinboard
* Favorites/stars aren't supported: if you favorite/star a bookmark in Pocket the script won't favorite/star it in Pinboard
* If you delete the most recently imported bookmark(s) from Pinboard but not from Pocket, the next time you run the script it'll re-import them
