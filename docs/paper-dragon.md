# Paper Dragon

An animated folded-paper dragon that grows with public and authorized private
GitHub work. The profile image links to an interactive portrait with language,
commit and streak inspection and exact progress to the next growth form.

See [setup, progression and privacy](living-dragon.md) for the current behavior
and credential requirements. The five source forms and their provenance are in
[the artwork guide](../assets/paper-dragon/README.md).

## Development

```sh
python3 -m unittest discover -s tests -v
node --check web/app.js
python3 scripts/build_site.py --source dragon --output _site
python3 -m http.server 8766 --bind 127.0.0.1 --directory _site
```

The site build uses the last generated aggregate output. To refresh real activity,
run Paper Dragon from the Actions tab, or provide DRAGON_ACTIVITY_TOKEN and
DRAGON_REPO_TOKENS through a local secret manager and run:

```sh
python3 scripts/paper_dragon.py --login dusk9998-max --output-dir dragon
```

Nightly updates run at 00:20 UTC. A failed collection preserves the last successful
artwork. Main runs deploy the interactive site after publication; branch runs
produce a preview artifact. All workflow actions are pinned to commit SHAs.
