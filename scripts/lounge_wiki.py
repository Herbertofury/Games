"""Document the shipped interactive lounge, without changing source-game facts."""
from pathlib import Path

def build(root,catalog):
    out=root/'wiki'
    page='''# Games Lounge: the library comes alive

**[Download the interactive library](https://github.com/Herbertofury/Games/releases/latest)** | [Browse all collections](Home)

A Steam-inspired interface for the same verified personal collection. The native wiki is a source directory; the portable HTML is the animated experience.

## Explore without losing your place

Cinematic spotlights with previous/next and a pause control. Personal shelves for recommendations, recently viewed, saved games and play-next. Searchable sidebar title lists contain every matching title, without viewport virtualization. Right-click a card to save it, mark it for later, watch its trailer or copy its exact store destination. Back and forward restore your actual filter combinations.

Big Picture enlarges the library and supports arrow-key card navigation. Ctrl+K opens appearance settings. Full screen is available when the browser permits it. Game details retain every original image, video, source, note, rating and mode-specific player count, with direct section navigation.

## The little guys are playing

The background is an original, live Canvas scene of tiny blobs tossing returning donuts. It is not a prerecorded clip and does not intercept library clicks. **Snackball** in the bottom bar opens its playable desktop window.

Move with WASD / arrows, aim with the pointer, and click or press Space to throw. Collect stars for 10 points; bonk the blobs for 25, with a bonus for consecutive hits. Their donuts cost 5 points when they hit you. Rounds last 60 active seconds. The best score stays on this device. A touch joystick and throw button support mobile. P pauses; Escape minimizes. Drag the title bar or resize the desktop window. Silly physics is optional.

Minimizing pauses an active round; it does not quietly run out your timer. The visual background can be switched off independently of playing the arcade.

## Motion and quiet controls

Settings include system/full/reduced/off animation, three atmosphere palettes, the living-desktop switch, spotlight rotation, hover screenshots, compact cards and optional interface sounds. Sound starts off. System reduced-motion preferences are respected by default. The game pauses when the browser loses focus; hidden tabs and open dialogs stop the scene loop. Focus mode removes ambient distractions and extra discovery shelves.

Existing favorites, notes, ratings and filters keep `games.library.v1`. Lounge preferences use `games.lounge.v2`; the arcade's best score uses `games.snackball.v1`. When browser storage is denied, the interface still runs with explicit session-only state. Existing personal-library exports continue to preserve the original game data; lounge settings and arcade scores are device-local preferences.

## Source and implementation

Steam-inspired, not a Steam client or account integration. Buttons do not pretend you own or installed games. Store actions remain exact external destinations. Official game artwork is preserved. The illustrated arcade is procedural UI/game code, not generated replacement game art. No trackers, scheduled scraping, external game engine or new CDN dependency is added.

Implementation: `site/lounge.js`, `site/lounge.css`, `site/arcade.js`. Build: `python3 scripts/build.py`. Runtime acceptance: `python3 scripts/lounge_qa.py`; prior genre suites remain in the publication gate.
'''
    (out/'Games-Lounge.md').write_text(page)
    home=out/'Home.md';s=home.read_text();home.write_text(s.replace('# A home for every great discovery','# A home for every great discovery\n\n**[The animated Games Lounge + desktop arcade](Games-Lounge)**',1))
    side=out/'_Sidebar.md';s=side.read_text();side.write_text(s.replace('- [Home](Home)','- [Home](Home)\n- [Animated lounge & arcade](Games-Lounge)',1))
