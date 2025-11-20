# Installing the extension

## Chrome

1. Go to `chrome://extensions/`
1. Turn on `Developer Mode`
1. Click `Load Unpacked`
1. Pick `extension` directory in this repo
1. Go to `Details` for the extension -> Turn off `Collect Errors`

## Firefox / Zen Browser

1. Run `bun run build` (opens browser to debugging page automatically)
1. Click `Load Temporary Add-on`
1. Select `manifest.json` from the `extension` directory

# Building

1. `bun run build`
1. **Chrome**: Go to `chrome://extensions/` -> Reload
1. **Firefox/Zen**: Extension reloads automatically with `bun run dev:firefox`

# Reference

## To run automatically

manifest.json:

```json
"content_scripts": [
    {
      "matches": [
        "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?statType=0"
      ],
      "js": ["dist/main.js"]
    }
  ]
```
