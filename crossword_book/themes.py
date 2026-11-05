"""Theme catalog shared by generation, publishing artwork, and the desktop app."""
CATALOG = {
    'dogs': ('Dog Lovers Crosswords','Tail-wagging fun, one clue at a time.','paw'),
    'cats': ('Cat Lovers Crosswords','Purr-fect puzzles for curious minds.','paw'),
    'wildlife': ('Wildlife Crosswords','Explore the wild, one clue at a time.','paw'),
    'animals': ('Animal Lovers Crosswords','A world of animals, one clue at a time.','paw'),
    'birds': ('Bird Lovers Crosswords','Let your curiosity take flight.','feather'),
    'fish': ('Fish Lovers Crosswords','Dive into a fresh crossword challenge.','fish'),
    'gardening': ('Gardening Crosswords','Let your curiosity grow, one clue at a time.','plant'),
    'baking': ('Baking Lovers Crosswords','Freshly baked fun for curious minds.','whisk'),
    'travel': ('Travel Lovers Crosswords','Explore the world, one clue at a time.','compass'),
    'space': ('Space Lovers Crosswords','Explore the universe, one clue at a time.','planet'),
    'christmas': ('Christmas Crosswords','Festive clues for cozy winter days.','snowflake'),
}
THEMES=tuple(CATALOG)
TITLES={name:values[0] for name,values in CATALOG.items()}
SUBTITLES={name:values[1] for name,values in CATALOG.items()}
MOTIFS={name:values[2] for name,values in CATALOG.items()}
ALIASES={'astronomy':'space','geography':'travel','travelandgeography':'travel','xmas':'christmas'}
