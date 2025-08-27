from destinations.instagram import InstagramDestination


content = {
    "Date": "",
    "Text": "Was geht?",
    "Time": "",
    "Status": "",
    "Image URLs": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Alois_Mentasti.jpg",
    "Video URLs": "",
    "Hashtags": "#was?",
}
dest = InstagramDestination()
status = dest.post(content=content)
print(f"STATUS: {status}")
