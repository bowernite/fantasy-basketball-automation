### Reference

#### To run automatically

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
