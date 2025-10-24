# Installing Chrome extension for the first time

1. Go to `chrome://extensions/`
1. Turn on `Developer Mode`
1. Click `Load Unpacked`
1. Pick `chrome-extension` directory in this repo
1. Go to `Details` for the extension -> Turn off `Collect Errors`

# Building

1. `bun run build`
1. Go to `chrome://extensions/` -> Reload

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
