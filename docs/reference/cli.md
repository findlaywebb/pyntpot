# The command line

The `pyntpot` command paints a GPX track as a map PNG. It is the entry point `pyntpot.maps.cli.main`. This page lists the command, its subcommand and every option the parser holds.

## Synopsis

```text
pyntpot [-h] command ...
pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT [--style STYLE] [--no-attribution] track
```

`command` is required and takes one value, `map`. The program reads the track, fills the fetch cache for any payload it lacks, paints the plates into the cache's plates directory for the track's key, letters the card with no annotations and composes the PNG. A cache that already holds the payloads sends no request. See [Cache layout](cache-layout.md) for the files it writes.

## Commands

### `map`

- Help text: paint a GPX track as a map PNG
- Description: reads a GPX file and writes one PNG. Fetches from Overpass and OpenTopoData when the cache lacks a payload, and identifies itself to them with `--contact`.

## Options of `pyntpot`

### `-h`, `--help`

- Argument: none
- Required: no
- Help text: show this help message and exit
- Description: prints the usage and exits with status 0.

## Arguments and options of `pyntpot map`

### `track`

- Form: positional
- Argument: a path to a GPX file
- Required: yes
- Help text: the GPX file to map
- Description: the route to paint. The track's bounding box, with the margin, decides what is fetched.

### `-o`, `--output`

- Argument: `OUTPUT`, a path
- Required: yes
- Help text: the PNG to write
- Description: where the composed map is saved. Missing parent directories are created.

### `--cache`

- Argument: `CACHE`, a path
- Required: yes
- Help text: the cache directory
- Description: the directory the fetch cache lives in. Created when missing. Nothing is resolved against the working directory.

### `--contact`

- Argument: `CONTACT`, a string
- Required: yes
- Help text: how the data providers' operators can reach you, such as an email address
- Description: sent to Overpass and OpenTopoData to identify the caller. It is not sent when the cache already holds every payload.

### `--style`

- Argument: `STYLE`, a path
- Required: no
- Help text: a TOML theme; the default theme when absent
- Description: a theme file with one table per style group, read with `Style.from_toml`. See [Style fields](style-fields.md). An unknown key is rejected.

### `--no-attribution`

- Argument: none
- Required: no
- Help text: leave the data attribution off the map
- Description: composes the map without the credit line. The duty to credit the data then moves to the caller.

### `-h`, `--help`

- Argument: none
- Required: no
- Help text: show this help message and exit
- Description: prints the usage of `map` and exits with status 0.

## Exit status

| Status | Meaning |
| --- | --- |
| 0 | The PNG was written. |
| 2 | A required argument is missing or an argument is not understood, as `argparse` exits. |

## What the command does not take

It takes no annotations, places or provider options, and it reads nothing from the environment. Progress is logged to standard error.
