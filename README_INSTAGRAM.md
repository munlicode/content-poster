# Posting Content to Instagram
## Create Business Profile (do not connect business) and add instagram as feature. Then go to usecases and Instagram Api -> Api with facebook login and choose """Manage content on Instagram
Add the listed content management permissions to create, publish and manage content with your Instagram account. Manage these and optional permissions and features on the Permissions and features page.

    instagram_basic
    instagram_content_publishing
    pages_read_engagement
    business_management
    pages_show_list"""
## Create Facebook page and link it to your instagram account
## Go to API explorer and generate new token, set all permissions that you selected in step 1.
## Get this token and go to access token debugger and debug it. Then extend and again debug. After that get this new token and in "granular scopes" section get id of "instagram_basic" -> this one goes to user_id in instagram json in token_storage.json
Now paste those two to token_storage.json 
# go to settings -> basic and copy app_id and app_secret and enter them into .env file fields
