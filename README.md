This is a horrible undocumented spaghetti monster but it seems to work fairly ok.

This was written with me in mind as the end user but it should be fairly straightforeward to use. It will prompt you to setup a tumblr aplication and get the oauth keys, its not tested but it should store them in ./.env for you too. I wanted to look at who i have blocked to thats wht the get data option does. it stores all the blocked blogs in a json file thats fun to look at. If i have the motivation it might be intresting to look at building some analysis scripts of who is blocked. When passing it the post url to block people from the output of the share button is what i wrote it for.

tumblr limits the usage of their blocks api endpoint to 60 requests/min and 20 things per page so it takes a while. 