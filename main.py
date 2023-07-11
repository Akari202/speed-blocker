from os import environ as env
import os
import dotenv
import pytumblr
import json
from time import sleep
from requests_oauthlib import OAuth1Session
from yaspin import yaspin


def new_oauth():
    print("Retrieve consumer key and consumer secret from http://www.tumblr.com/oauth/apps you can just put http://localhost:3000/__/auth/tumblr for the URLs")
    consumer_key = input("Paste the consumer key here: ").strip()
    consumer_secret = input("Paste the consumer secret here: ").strip()
    request_token_url = "http://www.tumblr.com/oauth/request_token"
    authorize_url = "http://www.tumblr.com/oauth/authorize"
    access_token_url = "http://www.tumblr.com/oauth/access_token"
    oauth_session = OAuth1Session(consumer_key, client_secret=consumer_secret)
    fetch_response = oauth_session.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    full_authorize_url = oauth_session.authorization_url(authorize_url)
    print("\nPlease go here and authorize:\n{}".format(full_authorize_url))
    redirect_response = input("Allow then paste the full redirect URL here:\n").strip()
    oauth_response = oauth_session.parse_authorization_response(redirect_response)
    verifier = oauth_response.get("oauth_verifier")
    oauth_session = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier
    )
    oauth_tokens = oauth_session.fetch_access_token(access_token_url)
    tokens = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "oauth_token": oauth_tokens.get("oauth_token"),
        "oauth_token_secret": oauth_tokens.get("oauth_token_secret")
    }
    return tokens

def save_tokens(tokens, path):
    with open(path, "w") as file:
        file.write(f"TUMBLR_CONSUMER_KEY = {tokens['consumer_key']}\n")
        file.write(f"TUMBLR_CONSUMER_SECRET = {tokens['consumer_secret']}\n")
        file.write(f"TUMBLR_OAUTH_TOKEN_KEY = {tokens['oauth_token']}\n")
        file.write(f"TUMBLR_OAUTH_TOKEN_SECRET = {tokens['oauth_token_secret']}\n")

def get_tokens():
    env_path = "./.env"
    if os.path.isfile(env_path):
        dotenv.load_dotenv()
        tokens = {
            "consumer_key": env["TUMBLR_CONSUMER_KEY"],
            "consumer_secret": env["TUMBLR_CONSUMER_SECRET"],
            "oauth_token": env["TUMBLR_OAUTH_TOKEN_KEY"],
            "oauth_token_secret": env["TUMBLR_OAUTH_TOKEN_SECRET"]
        }
    else:
        tokens = new_oauth()
        save = input("Do you want to save the oauth tokens to a .env file? [Y/n] ").strip().lower()
        if save == "" or save == "y":
            save_tokens(tokens, env_path)
    return tokens

def is_rate_limit(response):
    try:
        if response["meta"]["status"] == 429:
            return True
        else:
            return False
    except KeyError:
        return False

def block_post_likers(client):
    info = client.info()
    name = info["user"]["name"]
    post = input("What is the url to the post: ").strip()
    split_post = post[post.index("tumblr.com/") + 11:].split("/")
    blog = split_post[0]
    post_id = split_post[1]
    valid_options = ["id", "mode", "before_timestamp"]

    notes = client.notes(blog, post_id, mode="likes")
    blogs_to_block = []
    if is_rate_limit(notes):
        print("Rate limit currently exceeded please try again later (a few minutes to tomorrow)")
        return
    else:
        print("Begining to scrape likes")
    
    with yaspin(text="Finding") as spinner:
        while True:
            try:
                for i in notes["notes"]:
                    type = i["type"]
                    follow = i["followed"]
                    name = i["blog_name"]
                    if follow:
                        print(f"You follow {name}")
                    else:
                        blogs_to_block.append(name)
                next_link = notes["_links"]["next"]
                notes = client.notes(
                    blog, 
                    post_id, 
                    mode=next_link["query_params"]["mode"], 
                    before_timestamp=next_link["query_params"]["before_timestamp"]
                )
                if is_rate_limit(notes):
                    print("Rate limit currently exceeded, will atempt to block users anyway in 10s,,,")
                    sleep(10)
                    break

            except KeyError:
                break
        spinner.ok("✅ ")

    print(f"{blogs_to_block}\nYou have {len(blogs_to_block)} to block")
    if len(blogs_to_block) >= 0:
        with yaspin(text="Attempting to block,,,") as spinner:
            blogs_to_block_csv = ",".join(blogs_to_block)
            block_response = client.send_api_request(
                method="post",
                url=f"/v2/blog/{name}/blocks/bulk",
                params={"blocked_tumblelogs": blogs_to_block_csv},
                valid_parameters=["blocked_tumblelogs"]
            )
            spinner.ok("✅ ")
        print(f"Block response (empty is good): {block_response}")
    return

def get_blocked_blogs(client):
    info = client.info()
    name = info["user"]["name"]

    blocked_save_file = "./blocked.json"
    save = input(f"Would you like to save blocked tumblrs and update ./blocked.json? [Y/n] ").strip().lower()
    if save == "" or save == "y":
        if not os.path.isfile(blocked_save_file):
            blocked_tumblelogs = {
                "count": 0,
                "newest_uuid": "",
                "newest_timestamp": 0,
                "blocked_tumblelogs": []
            }
        else:
            with open(blocked_save_file, "r") as file:
                blocked_tumblelogs = json.load(file)

        blocked = client.send_api_request(
            method="get",
            url=f"/v2/blog/{name}/blocks",
            params={},
            valid_parameters=["limit", "offset"]
        )
        if is_rate_limit(blocked):
            print("Rate limit currently exceeded please try again in a few minutes")
            return
        else:
            print("Begining to read blocked blogs, tumblr is rate limited so this may take a while (roughly 0.05s per blocked account)")
        next_newest_uuid = blocked["blocked_tumblelogs"][0]["uuid"]
        next_newest_timestamp = blocked["blocked_tumblelogs"][0]["blocked_timestamp"]
        keep_paging = True

        with yaspin(text="Reading") as spinner:
            while keep_paging:
                try:
                    for i in blocked["blocked_tumblelogs"]:
                        uuid = i["uuid"]
                        timestamp = i["blocked_timestamp"]
                        if uuid == blocked_tumblelogs["newest_uuid"]:
                            keep_paging = False
                            continue
                        elif timestamp <= blocked_tumblelogs["newest_timestamp"]:
                            keep_paging = False
                            continue
                        else:
                            blocked_tumblelogs["blocked_tumblelogs"].append(i)
                    next_link = blocked["_links"]["next"]
                    sleep(1.1)
                    blocked = client.send_api_request(
                        method="get",
                        url=f"/v2/blog/{name}/blocks",
                        params={"offset": next_link["query_params"]["offset"]},
                        valid_parameters=["limit", "offset"]
                    )
                    if is_rate_limit(blocked):
                        print("Waiting 30s for rate limit cooldown")
                        sleep(30)
                        blocked = client.send_api_request(
                            method="get",
                            url=f"/v2/blog/{name}/blocks",
                            params={"offset": next_link["query_params"]["offset"]},
                            valid_parameters=["limit", "offset"]
                        )
                        if is_rate_limit(blocked):
                            print("Rate limit currently exceeded please try again later (a few minutes to tomorrow)")

                except KeyError:
                    keep_paging = False
                    break
            spinner.ok("✅ ")
        
        blocked_tumblelogs.update({
            "count": len(blocked_tumblelogs["blocked_tumblelogs"]),
            "newest_uuid": next_newest_uuid,
            "newest_timestamp": next_newest_timestamp
        })

        with open(blocked_save_file, "w") as file:
            file.write(json.dumps(blocked_tumblelogs, sort_keys=True, indent=4))
        return

def main():
    tokens = get_tokens() 
    client = pytumblr.TumblrRestClient(
        consumer_key=tokens["consumer_key"],
        consumer_secret=tokens["consumer_secret"],
        oauth_token=tokens["oauth_token"],
        oauth_secret=tokens["oauth_token_secret"]
    )

    while True:
        print("[B]: block people who liked a given post")
        print("[G]: get/update data on all blocked blogs")
        print("[Q]: exit the program")
        choice = input("What would you like to do? ").strip().lower()
        match choice:
            case "b":
                block_post_likers(client)
            case "g":
                get_blocked_blogs(client)
            case "q":
                return
            case _:
                pass

        # print(json.dumps(blocked, sort_keys=True, indent=4))

if __name__ == "__main__":
    main()