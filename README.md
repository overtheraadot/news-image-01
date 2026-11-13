# World News of Friday 13 November 2026 — make.fun news-image-01

A program that draws, in one image, the world's news of Friday
13 November 2026. It is a picture-editor front page: a large globe at
dusk in the centre, a white dove carrying an olive branch rising over
it, and seven gold-rimmed medallions around it, each standing for one
of the day's stories. No text anywhere — the stories are told in
pictures, so the image reads at a glance and still lands at ~300 px.

## The scene

- **The dove and the globe (lead story).** The dove with its olive
  branch over the world is the day's lead: the Ukraine peace talks —
  President Putin met US envoys Steve Witkoff and Jared Kushner in
  Moscow, Europe was promised a seat at the next round, and a prisoner
  exchange described as potentially the war's largest was planned.
- **Falling chart and chip (top left).** Nvidia founder and CEO Jensen
  Huang resigned; the shares fell about 16%.
- **Darkened envelope and warning mark (top right).** Microsoft Mail
  and Teams suffered a global outage.
- **Hospital cross and candle (left).** An Israeli strike on a Khan
  Younis hospital killed six people, including a surgeon.
- **Storm cloud, rain and waves (right).** Storm Charles brought severe
  weather to Portugal.
- **Football (bottom left).** England beat Croatia to reach the Nations
  League quarter-finals.
- **LNG tanker and sea mine (bottom right).** An LNG tanker was hit by
  a mine in the Strait of Hormuz.
- **Smart glasses (bottom centre).** Google deployed a new search model,
  "Gemini 4 Hydrogen", and opened smart-glasses preorders.

## How to run

```sh
python3 main.py
```

Writes `entry.png` (1024×1024, PNG) to the current directory, or to
`$MAKEFUN_OUTPUT_DIR` when that is set — the harness runs it as
`MAKEFUN_OUTPUT_DIR=/output python3 main.py`.

## Determinism

The program uses only the Python 3 standard library (zlib for the PNG
encoder), reads no files, touches no network, and draws from a fixed
seed, so every run writes byte-identical output.
