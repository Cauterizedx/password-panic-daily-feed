# Password Panic daily feed

This public GitHub Pages repository supplies the five-letter daily Wordle answer used by the Password Panic VRChat world.

The VRChat-safe endpoint is:

`https://cauterizedx.github.io/password-panic-daily-feed/current.txt`

`current.txt` contains exactly one uppercase, five-letter word followed by a newline. `meta.json` records the puzzle date and update timestamp. A scheduled GitHub Action refreshes the files from the New York Times Wordle endpoint and refuses to publish malformed data.

The updater runs hourly so it recovers automatically from delayed puzzle publication or a transient request failure. If the online feed is unavailable, the world uses its packaged fallback rather than making a game unwinnable.

This project is not affiliated with or endorsed by The New York Times or Wordle.
