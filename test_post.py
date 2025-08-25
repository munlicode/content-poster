from destinations.threads import ThreadsDestination

destination = ThreadsDestination()

item = {"text": "Alles hat einen Sinn."}
success = destination.post(item)

if success:
    print("Published successfully")
else:
    print("Failed to publish")
"""

RIDD="?grant_type=th_exchange_token&client_secret=294d21132873dccca16cb7cecdd76062&access_token=THAAQBGVHbKzBBUVJ3ZAHNRYjZAkaHRocWRvVmx4YWI5UjM4c0ZArek9Fa3JJMVBhWkpySkhvcXBybEdlRVd0OHVuRXR0MUpZARWV2cURzVUF3ZAHNzWWN3emVwcEN3aWtocmFjeU9GVjVoZA3loOEdTZAzdDVUNHME9FazQwajBYeTd2Y3FRbENyNjVKMzZA5NmQyZAzR5elFaODUtRzZALWk5oOWllUXc2aVUyWWcZD"
DAAA="{"access_token": "THAAQBGVHbKzBBUVFGWm9kVFVtM2xia0g4ZAS1UcV9OYzZAMRnBBeXJoei1aSFUtel9NTUxNZAWJnR2p2R1dpelFGSm9UdGhHUHo3RTVkbVNtVnZASbGFMQTBSYU0wVk1lSjFfblNHanRaeHZAHdXdSbzM0d2ZAQYVo1aDJxZA1pRalJmQ3FpdwZDZD","token_type": "bearer","expires_in": 5183999}"
"""
