"""Distinct themed puzzle titles with a random stream separate from grid filling."""
import random

_BANKS = {
    'dogs': '''Paws and Play|A Loyal Companion|Walk in the Park|Happy Tails|The Nose Knows|Fetch Some Fun|Puppy Playtime|Best Friends Forever|Pawprints at Dawn|Off the Leash|A Wagging Welcome|Canine Capers|The Daily Walk|Barks and Beyond|Four-Legged Friends|A Treat in Store|The Sniffing Trail|Dog Days of Fun|Paws for Thought|The Great Fetch|A Faithful Friend|Tail-Wagging Times|At the Dog Park|A Cozy Kennel|The Pack Is Back|A Nose for Adventure|Playful Pups|The Good Dog Club|Through the Garden Gate|Ready for a Walk|The Pawprint Path|A Day with My Dog|Sit, Stay, Solve|The Friendly Pack|A Bowl of Happiness|The Curious Canine|A Well-Earned Treat|All Ears and Paws|The Wagging Trail|A Bark in the Park|The Canine Connection|A Dog's Day Out|Home Is Where the Dog Is|The Fetching Challenge|New Tricks|A Pawfect Afternoon|Friends on Four Paws|The Happy Hound|A Lead to Follow|Puppy Love''',
    'cats': '''The Curious Cat|Whisker Wonders|Paws in the Sun|A Cozy Catnap|The Purring Hour|Feline Friends|A Window Seat|The Midnight Prowl|Purrs and Puzzles|Nine Lives of Fun|The Quiet Pounce|A Ball of Yarn|Whiskers at Work|The Velvet Paw|A Sunny Windowsill|Cats at Play|The Secret Garden Cat|A Tail of Curiosity|The Gentle Purr|An Afternoon Catnap|Feline Fine|The Climbing Tree|A Kitten's World|The Watchful Whiskers|Moonlight and Meows|A Place to Perch|The Cat's Meow|Soft Paws, Sharp Minds|The Playful Pounce|A Purrfect Companion|The Scratching Post|The Curious Kitten|The Feline Connection|A Basket of Comfort|The Nighttime Explorer|Whiskers in the Wind|A Quiet Corner|The Catnap Club|Eyes in the Moonlight|A Furry Welcome|Paws on Patrol|The Graceful Leap|A Little Mischief|The Purring Path|A Cat's Day Out|The Cozy Cushion|Chasing Sunbeams|A Whiskered Welcome|The Silent Stalker|Purrfect Puzzle Time''',
    'wildlife': '''Into the Wild|Tracks at Dawn|The Hidden Trail|Forest Whispers|A Wild Encounter|Beyond the Treeline|The Woodland Watch|Footprints in the Mud|The Quiet Clearing|Life on the Riverbank|A Night in the Forest|Wonders of the Wild|The Mountain Path|The Wild Neighbors|A Glimpse of Nature|The Meadow Watch|Under the Canopy|The Secret Burrow|Across the Open Plain|The Wilderness Trail|Dusk in the Woods|Nature's Footprints|The Hidden Habitat|Along the Woodland Edge|A Forest Adventure|Wild at Heart|The River's Edge|The Silent Wilderness|A Walk on the Wild Side|The Moonlit Meadow|Hidden in the Reeds|Beyond the Clearing|The Watchful Woods|A Trail of Discovery|The Wild World|Whispers at Dusk|The Northern Forest|A Refuge in the Wild|The Marshland Mystery|The Wildlife Watch|Out in the Open|The Ancient Woodland|A Journey into Nature|The Quiet River|The Wilderness Connection|A Place in the Wild|The Roaming Trail|The Nature Notebook|Through the Undergrowth|The Great Outdoors''',
    'animals': '''The Animal Kingdom|Creatures Great and Small|A World of Wonders|The Creature Club|Wild and Wonderful|The Living World|Paws, Claws, and More|Nature's Neighbors|The Great Animal Adventure|A Creature Feature|Across the Animal World|Fur and Feathers|The Curious Creature|The Animal Connection|An Amazing Menagerie|Every Creature Counts|The Habitat Hunt|The Wonder of Life|A World of Wildlife|The Mighty and the Mini|Animal Encounters|The Nature Trail|A Creature's Journey|The Great Migration|Around the Waterhole|The World We Share|Nature's Marvels|All Shapes and Sizes|A Kingdom of Clues|The Creature Chronicle|Life in the Treetops|The Animal Atlas|From Forest to Field|Nature's Playground|The Wild Parade|A Curious Collection|The Living Landscape|Big Paws, Small Paws|The Creature Quest|The Natural World|A Walk with Animals|The Animal Explorer|Life on Four Legs|The Gentle Giants|The Great Gathering|A Wild Discovery|The Creature Connection|Nature's Hidden Gems|The Animal Notebook|Our Animal Friends''',
    'birds': '''Wings of Wonder|The Dawn Chorus|Feathered Friends|A Song in the Trees|The Morning Nest|Taking Flight|The Birdwatcher's Trail|On the Wing|A Feathered Welcome|The Sky Above|The Woodland Song|Wings over Water|The Nesting Place|A Flash of Feathers|The Migration Route|A Bird's-Eye View|The Garden Chorus|The Open Sky|A Perch in the Sun|The Feathered Flock|Songs at Sunrise|The Winged World|A Walk with Wings|The Quiet Birdhide|Feathers in the Breeze|The Roosting Hour|A Nest of Clues|The Birdsong Path|High in the Treetops|The Shorebird Watch|The Flight of Fancy|A Wing and a Song|The Birding Notebook|Through the Reeds|The Meadow Chorus|A Sky Full of Wings|The Feathered Explorer|The Early Bird|The Lakeside Watch|The Gentle Glide|A Song on the Breeze|The Hidden Nest|The Winged Wanderer|The Feather Trail|From Branch to Branch|The Evening Chorus|A World of Birds|The Coastal Flock|The Birdwatching Hour|Where the Birds Sing''',
    'fish': '''Beneath the Surface|The Underwater World|A School of Clues|Along the Riverbed|The Reef Explorer|Fins and Friends|The Quiet Stream|A Splash of Discovery|The Ocean Current|Life in the Pond|The River's Journey|A World of Fins|The Coral Corner|Swimming with Clues|The Freshwater Trail|The Deep Blue|A Fish's Tale|The Hidden Lagoon|The Tide Pool|The Aquarium Window|A Ripple of Wonder|The Flowing Stream|The Ocean Notebook|A Shoal of Surprises|The Lakeside Adventure|The Reef Connection|Into the Blue|The River Explorer|The Fin Trail|A Quiet Backwater|The Underwater Garden|The Coastal Current|The Pond Patrol|A Glimpse Below|The Streamside Watch|The Blue Horizon|Where the Fish Swim|The Waterway Quest|A Current of Curiosity|The Shimmering Shoal|The Ocean Explorer|From River to Reef|A Dive into Discovery|The Freshwater World|The Hidden Cove|The Silver Scales|The Lagoon Lookout|The Tidal Trail|The Fishkeeper's Corner|The Wonders Below''',
}
_BANKS.update({'gardening': 'Seeds of Curiosity|A Garden in Bloom|Roots and Shoots|The Potting Bench|Among the Flowers|A '
              'Patch of Green|The Garden Gate|Spring in the Soil|A Blooming Good Day|The Seedling '
              "Trail|Under the Apple Tree|The Gardener's Corner|A Bed of Roses|The Greenhouse Door|A Basket "
              'of Harvests|The Compost Corner|Tending the Borders|Petals and Paths|The Growing Season|A '
              'Little Green Magic|The Herb Garden|From Seed to Sprout|A Quiet Garden Walk|The Kitchen '
              'Garden|The Watering Hour|Beneath the Leaves|The Cottage Garden|A Sunny Border|The Garden '
              'Notebook|The Secret Seed|A Tangle of Vines|The Shady Patch|The Flowering Trail|The Morning '
              'Gardener|The Root of the Matter|A Place to Grow|The Weekend Gardener|The Fresh Harvest|The '
              'Garden Explorer|An Orchard Afternoon|The Garden Path|The Pruning Hour|A New Leaf|The Raised '
              'Bed|The Pollinator Patch|The Tender Shoot|A Handful of Seeds|The Garden Retreat|The Green '
              'Thumb Club|A Season of Growth',
 'baking': "Sweet Success|The Flour Trail|A Golden Crust|From Oven to Table|The Mixing Bowl|A Baker's "
           'Morning|The Pastry Corner|A Pinch of Spice|The Warm Loaf|A Spoonful of Sugar|The Cookie '
           'Jar|Batter and Butter|The Kneading Hour|A Fresh Batch|The Secret Ingredient|A Slice of '
           "Delight|The Cake Stand|A Dusting of Flour|The Rolling Pin|A Baker's Notebook|The Cooling "
           'Rack|The Sweetest Clue|A Bowl of Possibilities|The Sunday Bake|The Sourdough Story|The Golden '
           'Oven|A Touch of Vanilla|The Pastry Basket|The Rise and Shine|A Crumb of Curiosity|The Icing on '
           'the Cake|The Biscuit Tin|A Homemade Treat|The Bread Basket|The Dessert Table|The Cinnamon '
           'Swirl|A Sprinkle of Fun|The Baking Bench|A Well-Proofed Puzzle|The Little Patisserie|The '
           "Chocolate Corner|A Batch of Smiles|The Pie Window|A Soft Center|The Flaky Layers|The Baker's "
           'Challenge|A Taste of Home|The Perfect Dough|A Sweet Discovery|The Final Frosting',
 'travel': 'Across the Map|The Scenic Route|A Passport to Puzzles|The Departure Lounge|A Ticket to '
           "Explore|The Open Road|A Journey of Discovery|The Weekend Escape|The Traveler's Notebook|Beyond "
           'the Horizon|A Window Seat|The Hidden Destination|The Coastal Road|A City to Discover|The '
           'Mountain Pass|The Railway Journey|The Harbor Lights|A New Direction|The Local Guide|A Postcard '
           'Home|The Island Escape|The Compass Point|A Day in the Capital|The Winding Path|The World '
           'Awaits|The Road Less Taken|A Bag of Memories|The Next Stop|The Riverside Walk|A Glimpse '
           "Abroad|The Arrival Gate|The Faraway Place|A Room with a View|The Mapmaker's Trail|The Long "
           'Weekend|A World of Clues|The Lakeside Stay|The Border Crossing|An Ocean Away|The City Break|The '
           'Friendly Hostel|A Change of Scenery|The Walking Tour|The Great Getaway|A Place on the Map|The '
           "Traveler's Trail|The Last Connection|A Journey to Remember|The Destination Ahead|The Homeward "
           'Route',
 'space': "Among the Stars|A Cosmic Journey|The Orbital Path|Beyond the Moon|The Stargazer's Night|A Window "
          "on the Universe|The Planetary Trail|The Night Sky|A Celestial Discovery|The Rocket's Journey|The "
          'Lunar Landscape|The Galaxy Next Door|A Stellar Challenge|The Observatory Door|The Space '
          'Explorer|A Trail of Starlight|The Distant Worlds|The Solar Neighborhood|A Mission of '
          'Curiosity|The Cosmic Notebook|The Brightest Star|A Question of Gravity|The Telescope View|The '
          "Midnight Sky|A Giant Leap of Thought|The Comet's Tail|The Ringed World|A Universe of Clues|The "
          "Star Cluster|The Astronomer's Corner|A Journey through Space|The Launch Window|The Hidden "
          'Nebula|The Lunar Adventure|A Sky Full of Wonder|The Celestial Compass|The Great Beyond|A Planet '
          'to Discover|The Milky Way Trail|The Orbiting Observer|A Glimmer in the Dark|The Quiet Cosmos|The '
          'Spaceflight Story|A Night at the Observatory|The Stellar Map|The Next Frontier|A Solar '
          'Surprise|The Moonlit Mission|The Cosmic Connection|An Astral Afternoon',
 'christmas': 'Season of Joy|A Festive Welcome|Under the Mistletoe|The Christmas Hearth|A Stocking Full of '
              'Clues|The Winter Gathering|A Merry Little Puzzle|The Caroling Hour|The Gift of Curiosity|A '
              'Cozy Christmas|The Holly and the Clues|The Snowflake Trail|A Season to Share|The Twinkling '
              'Tree|The Christmas Table|A Parcel of Puzzles|The Midnight Bells|The Festive Fireplace|A Warm '
              'Winter Wish|The Holiday Notebook|The Christmas Market|A Ribbon of Wonder|The Yuletide '
              'Trail|The Candlelit Window|A Touch of Tinsel|The Christmas Kitchen|The Sleigh Ride|A Bowl of '
              'Cheer|The December Doorway|The Ornament Box|A Quiet Christmas Eve|The Gingerbread House|The '
              'Fireside Gathering|The North Pole Trail|A Present to Unwrap|The Festive Choir|A Christmas '
              "Carol|The Winter Welcome|The Christmas Star|A Little Holiday Magic|The Season's Greetings|The "
              'Holiday Home|A Festive Feast|The Christmas Countdown|A Wish for Peace|The Merry Gathering|The '
              'Evergreen Corner|A Christmas to Remember|The Final Gift|The Joy of Christmas'})
_CONTEXTS = {
    'dogs': ('Pawprint','Canine','Puppy','Hound','Tail-Wagging','Dog Park','Kennel','Fetching'),
    'cats': ('Whisker','Feline','Kitten','Catnap','Purring','Moonlit','Velvet Paw','Sunbeam'),
    'wildlife': ('Woodland','Wilderness','Forest','Meadow','Riverbank','Marshland','Wildlife','Mountain'),
    'animals': ('Animal','Creature','Habitat','Nature','Menagerie','Kingdom','Wild World','Safari'),
    'birds': ('Feathered','Birdsong','Winged','Nesting','Skyward','Shorebird','Treetop','Birdwatching'),
    'fish': ('Underwater','Freshwater','Ocean','River','Reef','Lagoon','Aquarium','Streamside'),
}
_CONTEXTS.update({'gardening': ('Garden', 'Greenhouse', 'Seedling', 'Blooming', 'Herbal', 'Orchard', 'Meadow', 'Potting'),
 'baking': ('Baker', 'Pastry', 'Sourdough', 'Golden Crust', 'Sweet', 'Chocolate', 'Cookie', 'Homemade'),
 'travel': ('Traveler', 'Coastal', 'Overland', 'City', 'Island', 'Mountain', 'Passport', 'Scenic'),
 'space': ('Cosmic', 'Stellar', 'Lunar', 'Solar', 'Galactic', 'Orbital', 'Planetary', 'Astral'),
 'christmas': ('Festive', 'Yuletide', 'Christmas', 'Winter', 'Holly', 'Candlelit', 'December', 'Snowflake')})
_ENDINGS = ('Discovery','Adventure','Quest','Journey','Challenge','Exploration','Secrets',
            'Wonders','Treasures','Trail','Escape','Delight','Mystery','Revelations','Pursuit','Retreat')


def titles_for(theme, count, seed):
    """Unique titles for any book length, reproducible without changing its grids."""
    if theme not in _BANKS:
        raise ValueError('Unknown theme')
    if not isinstance(count,int) or count<0:
        raise ValueError('Title count must be a nonnegative integer')
    rng=random.Random(f'{theme}:{seed}:puzzle-titles-v1')
    base=_BANKS[theme].split('|')
    rng.shuffle(base)
    extended=[f'{context} {ending}' for context in _CONTEXTS[theme] for ending in _ENDINGS]
    rng.shuffle(extended)
    pool=list(dict.fromkeys(base+extended))
    result=pool[:count]
    collection=2
    while len(result)<count:
        result.extend(f'{title}: Collection {collection}' for title in pool[:count-len(result)])
        collection+=1
    return result


def assign_puzzle_titles(book, excluded_titles=None):
    """Also upgrade saved books; preserve existing user-edited titles."""
    existing=[p['title'] for p in book['puzzles'] if p.get('title')]
    used={title.casefold() for title in existing}
    if len(used)!=len(existing):
        raise ValueError('Puzzle titles must be unique within a book')
    used.update(title.casefold() for title in (excluded_titles or ()))
    candidates=iter(titles_for(book['theme'],len(book['puzzles'])+len(used),book.get('seed',1)))
    for puzzle in book['puzzles']:
        if not puzzle.get('title'):
            title=next(candidates)
            while title.casefold() in used:
                title=next(candidates)
            puzzle['title']=title
            used.add(title.casefold())
