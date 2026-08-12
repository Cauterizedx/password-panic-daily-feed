# Password Panic live-data feed

This public GitHub Pages repository supplies frozen online data used by the Password Panic VRChat world.

VRChat-safe endpoints:

- `https://cauterizedx.github.io/password-panic-daily-feed/current.txt`
- `https://cauterizedx.github.io/password-panic-daily-feed/live-data.txt`

`current.txt` remains the backwards-compatible five-letter Wordle endpoint. `live-data.txt` is a simple `KEY=VALUE` snapshot containing Wordle, five delayed/latest-close stock quotes, global weather, exchange rates, the strongest USGS earthquake from the last day, an On This Day event, and one multiple-choice trivia question.

The world downloads the GitHub Pages file once, freezes it for that room instance, and synchronizes the selected answers to all players. Each upstream section updates independently. If a provider is temporarily unavailable, the updater preserves that section's last valid values instead of publishing blanks.

The updater runs hourly. If the GitHub feed itself is unavailable, the world uses its packaged snapshot so the game remains solvable. Market values are informational delayed/latest-close figures for a party game, not financial advice.

The periodic table displayed in the room is cached at `assets/Periodic-Table.png`. It comes from [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Periodic-Table.png), where the author dedicated the image to the public domain under CC0 1.0.

This project is not affiliated with or endorsed by The New York Times, Wordle, Yahoo, Open-Meteo, Wikimedia, Open Trivia DB, Frankfurter, or USGS.
