item = {
    "Date": "2025-08-25",
    "Time": "0:35",
    "Status": "",
    "Text": "Nur das Bild",
    "Image URLs": "",  # "https://i.etsystatic.com/27342201/r/il/2bef8e/5404598160/il_fullxfull.5404598160_ji5z.jpg",
    "Video URLs": "",
    "Hashtags": "#Leben",
    "Hashtags with TEXT": "FALSE",
    "Do Not Post Media on Threads": "FALSE",
    "Post on Instagram": "false",
    "Post on Threads": "TRUE",
    "Local Image Path": "/home/munlicode/Pictures/random/photo_2025-07-26_17-02-21.jpg,/home/munlicode/Pictures/Wallpapers/karikatur-von-drei-geschaftsleute-in-einem-buro-mit-dem-schild-das-heutige-thema-ist-weg-von-dem-problem-suchen-eew676.jpg",
    # "Local Video Path": "/media/munlicode/data/temp/Big_Buck_Bunny_1080_10s_1MB.mp4",
    "row_number": 2,
}

from destinations.instagram import InstagramDestination
from destinations.threads import ThreadsDestination

tr_dest = ThreadsDestination()
dest = InstagramDestination()
from config import settings

if item.get(settings.POST_ON_INSTAGRAM_COLUMN_NAME) == "TRUE":
    result = dest.post(item)
    print(result)

elif item.get(settings.POST_ON_THREADS_COLUMN_NAME) == "TRUE":
    result = tr_dest.post(item)
    print(result)
