from os import environ as env
import dotenv
import pytumblr
import json

dotenv.load_dotenv()
TUMBLR_CONSUMER_KEY = env["TUMBLR_CONSUMER_KEY"]
TUMBLR_CONSUMER_SECRET = env["TUMBLR_CONSUMER_SECRET"]
TUMBLR_OAUTH_TOKEN = env["TUMBLR_OAUTH_TOKEN_KEY"]
TUMBLR_OAUTH_TOKEN_SECRET = env["TUMBLR_OAUTH_TOKEN_SECRET"]

def main():
    client = pytumblr.TumblrRestClient(
        consumer_key=TUMBLR_CONSUMER_KEY,
        consumer_secret=TUMBLR_CONSUMER_SECRET,
        oauth_token=TUMBLR_OAUTH_TOKEN,
        oauth_secret=TUMBLR_OAUTH_TOKEN_SECRET
    )
    post = input("What is the url to the post: ")
    split_post = post[post.index("tumblr.com/") + 11:].split("/")
    blog = split_post[0]
    post_id = split_post[1]
    valid_options = ["id", "mode", "before_timestamp"]

    notes = client.notes(blog, post_id, mode="likes")
    blogs_to_block = []
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

        except KeyError:
            break

    print(f"You have {len(blogs_to_block)} to block\n{blogs_to_block}")
    if len(blogs_to_block) >= 0:
        blogs_to_block_csv = ",".join(blogs_to_block)
        block_response = client.send_api_request(
            method="POST",
            url="/v2/blog/akari202/blocks/bulk",
            params={"blocked_tumblelogs": blogs_to_block_csv},
            valid_parameters=["blocked_tumblelogs"]
        )
        print(f"Attempting to block,,, response: {block_response}")
    
    # print(json.dumps(blocked, sort_keys=True, indent=4))
    

if __name__ == "__main__":
    main()