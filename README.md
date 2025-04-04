Pocket to Pinboard Sync
=======================

Syncs your bookmarks from [Pocket](https://getpocket.com/) to [Pinboard](https://pinboard.in/).

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
* Run it continuously on GitHub Actions

Limitations
-----------

* Only syncs from Pocket to Pinboard, not the other way round. Any changes to bookmarks in Pinboard won't be synced to Pocket
* Bookmarks that already exist in Pinboard won't be updated:
  * If you manually save a bookmark in both Pinboard and Pocket the script won't update that bookmark in Pinboard. For example any tags from Pocket won't be synced
  * If you run the script and it syncs a bookmark to Pinboard, then you edit the bookmark in Pocket (e.g. changing its tags) and run the script again, the bookmark won't be re-synced
* Bookmarks deleted from Pocket won't be deleted from Pinboard
* Favorites/stars aren't supported: if you favorite/star a bookmark in Pocket the script won't favorite/star it in Pinboard
* If you delete the most recently imported bookmark(s) from Pinboard but not from Pocket, the next time you run the script it'll re-import them

Usage
-----

To get a Pocket consumer key and access token follow Pocket's instructions: https://getpocket.com/developer/docs/authentication.
This blog post is also helpful: https://www.jamesfmackenzie.com/getting-started-with-the-pocket-developer-api/.

To get a Pinboard API token go to: https://pinboard.in/settings/password.

### Using locally

```console
$ python -m venv .venv
$ .venv/bin/pip install -r requirements.txt
$ POCKET_CONSUMER_KEY=$YOUR_POCKET_CONSUMER_KEY POCKET_ACCESS_TOKEN=$YOUR_POCKET_ACCESS_TOKEN PINBOARD_AUTH_TOKEN=$YOUR_PINBOARD_AUTH_TOKEN .venv/bin/python pocket_to_pinboard.py
```

### Using on GitHub Actions

To run the script continuously on GitHub Actions:

1. Create a GitHub repo

2. Create three [GitHub Actions secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) in the repo: `POCKET_CONSUMER_KEY`, `POCKET_ACCESS_TOKEN` and `PINBOARD_AUTH_TOKEN`.

3. Create a `.github/workflows/sync.yml` file in the repo, with these contents (replace `<COMMIT_ID>` with the latest commit ID from this repo's `main` branch):

   ```yml
   # .github/workflows/sync.yml
   on:
     schedule:
       - cron: '0 */3 * * *'
     workflow_dispatch:
   concurrency:
     group: sync
   jobs:
     sync:
       uses: seanh/pocket_to_pinboard/.github/workflows/sync.yml@<COMMIT_ID>
       secrets:
         POCKET_CONSUMER_KEY: ${{ secrets.POCKET_CONSUMER_KEY }}
         POCKET_ACCESS_TOKEN: ${{ secrets.POCKET_ACCESS_TOKEN }}
         PINBOARD_AUTH_TOKEN: ${{ secrets.PINBOARD_AUTH_TOKEN }}
     keepalive:
       needs: sync
       runs-on: ubuntu-latest
       steps:
       - run: gh workflow enable --repo '${{ github.repository }}' '.github/workflows/sync.yml'
         env:
           GH_TOKEN: ${{ secrets.github_token }}
   ```

4. If pinning the version of `sync.yml` that you're calling to a specific `<COMMIT_ID>`, as in the example above, you may want to add a `.github/dependabot.yml` file like this to get Dependabot to send you updated PRs whenever I update this repo:

   ```yml
   # .github/dependabot.yml
   version: 2
   updates:
   - package-ecosystem: "github-actions"
     directory: "/"
     schedule:
       interval: "daily"
   ```
