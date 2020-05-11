#!/usr/bin/python3.7
import json
import aiohttp
import discord
from discord.ext import commands, tasks
from q_bank_db import DB
from cflc_util import handle_cf, handle_lc
import datetime
import traceback
import os

# globals
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))
postdaily = {
    'difficulty': 0,
    'channelid': os.environ.get('Q_CHANNEL_ID', -1)
}


#######################################
#               EVENTS               #
#######################################

@bot.event
async def on_ready():
    print("Bot Online!")
    post_a_question.start()


#######################################
#              COMMANDS               #
#######################################

@bot.command(description="Insult someone", usage="<@user>")
async def insult(ctx, member: discord.Member = None):
    """insult someone"""
    async with ctx.typing():
        member = member or ctx.message.author
        async with aiohttp.ClientSession() as session:
            async with session.get('https://insult.mattbas.org/api/insult') as resp:
                await ctx.send(f"{member} {await resp.text()}")


@bot.command(description="get a question with difficulty and/or tag", usage="<difficulty_level> [<tag>]")
async def ques(ctx, diff: int = None, tag: str = None):
    """get a question with difficulty and/or tag"""
    async with ctx.typing():
        with DB() as db:
            qdata = db.get_ques(diff=diff, tag=tag)
            if not qdata:
                await ctx.send(f"No question with given parameter found.")
                return
        if qdata['source'] == 'LC':
            embed = make_embed_lc(qdata, handle_lc(qdata))
        else:
            embed = make_embed_cf(qdata, handle_cf(qdata))
        await ctx.send(f"Here's a question with difficulty level of : {diff}", embed=embed)


@bot.command(description="Valid values for difficulty and tags", usage="")
async def argh(ctx):
    """Valid values for difficulty and tags arguments"""
    async with ctx.typing():
        await ctx.send(
            f"**Difficulty:**\n ***0 - 11, 13***\n 0: easiest, 11: hardest, 13: unknown\n\n\n**Tags**:\n```\n "
            f"- rolling hash\n - dynamic programming\n - bit manipulation\n - ordered map\n - reservoir "
            f"sampling\n - graph\n - topological sort\n - sort\n - suffix array\n - geometry\n - array\n - "
            f"binary search tree\n - breadth-first search\n - brainteaser\n - minimax\n - recursion\n - "
            f"design\n - greedy\n - sliding window\n - string\n - backtracking\n - queue\n - rejection "
            f"sampling\n - segment tree\n - random\n - divide and conquer\n - binary indexed tree\n - heap\n - "
            f"depth-first search\n - two pointers\n - union find\n - hash table\n - binary search\n - line "
            f"sweep\n - trie\n - math\n - tree\n - memoization\n - linked list\n - stack\n - binary search\n - "
            f"bitmasks\n - data structures\n - math\n - 2-sat\n - string suffix structures\n - schedules\n - "
            f"probabilities\n - strings\n - shortest paths\n - brute force\n - divide and conquer\n - "
            f"geometry\n - ternary search\n - expression parsing\n - interactive\n - games\n - dp\n - dfs and "
            f"similar\n - constructive algorithms\n - *special\n - graphs\n - greedy\n - combinatorics\n - two "
            f"pointers\n - meet-in-the-middle\n - chinese remainder theorem\n - matrices\n - graph matchings\n "
            f"- sortings\n - number theory\n - dsu\n - flows\n - fft\n - trees\n - implementation\n - "
            f"hashing\n```")


@bot.command(description="Get hints (leetcode only) and tags for questions", usage="<question_id>")
async def hint(ctx, qid: str = None):
    """Get hints (leetcode only) and tags for questions"""
    async with ctx.typing():
        with DB() as db:
            data = db.get_hint(qid)
            h = "\n".join(json.loads(data['hints']))
            t = "\n".join(data['tags'].split(","))
            await ctx.send(f"**Hints:**\n||{h or 'None'}||\n\n**Tags:**\n||{t or 'None'}||")


@bot.command(description="Set daily questions difficulty level", usage="<difficulty>")
async def setdiff(ctx, diff: int):
    """Set daily questions difficulty level"""
    async with ctx.typing():
        if 'botdev' in [y.name.lower() for y in ctx.author.roles] and diff >= 0 and diff <= 11:
            postdaily['difficulty'] = diff
            await ctx.send(f"New question difficulty: {diff}")
        else:
            await ctx.send(f"Only ***botdev*** can set global questions difficulty (0-11)")


@bot.command(description="When will be the next question posted.", usage="")
async def nextqs(ctx):
    """When will be the next question posted."""
    async with ctx.typing():
        await ctx.send(f"Next question will be posted at: {post_a_question.next_iteration}")


@bot.command(description="", usage="")
async def starttask(ctx):
    if 'botdev' in [y.name.lower() for y in ctx.author.roles]:
        post_a_question.stop()
        post_a_question.start()


@bot.command(description="post a question for everyone")
async def postques(ctx):
    await unpin_old_message()
    await post_a_question()
    await pin_new_message()


#######################################
#         Utility Function           #
#######################################
def make_embed_cf(qdata, cfdata):
    url = f"https://codeforces.com/problemset/problem/{qdata['id'][:-1]}/{qdata['id'][-1]}"
    embed = discord.Embed(title=qdata['title'], colour=discord.Colour(0x3b67e7), url=url,
                          description=cfdata['description'], timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url="https://sta.codeforces.com/s/77932/images/codeforces-logo.png")
    embed.set_author(name=f"CodeForces: {qdata['id']}", url=url,
                     icon_url="https://sta.codeforces.com/s/77932/images/codeforces-logo.png")
    for indx, tc in enumerate(cfdata['testcases']):
        embed.add_field(name=f'input {indx + 1}', value=tc['input'], inline=True)
        embed.add_field(name=f'output {indx + 1}', value=tc['output'], inline=True)
        # embed.add_field(name="\u200b", value='\u200b')

    for k, v in cfdata['header'].items():
        embed.add_field(name=k, value=v, inline=True)

    for k, v in json.loads(qdata['stats']).items():
        embed.add_field(name=k, value=v, inline=True)

    embed.add_field(name="Difficulty", value=f"{qdata['difficulty']}")
    return embed


def make_embed_lc(qdata, content):
    url = f"https://leetcode.com/problems/{'-'.join(qdata['title'].lower().split())}"
    logo_url = "https://assets.leetcode.com/static_assets/public/images/LeetCode_logo_rvs.png"
    embed = discord.Embed(title=qdata['title'], colour=discord.Colour(0x3b67e7), url=url, description=content,
                          timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url=logo_url)
    embed.set_author(name=f"Leetcode: {qdata['id']}", url=url, icon_url=logo_url)
    embed.add_field(name="Difficulty", value=f"{qdata['difficulty']}")
    for k, v in json.loads(qdata['stats']).items():
        embed.add_field(name=k, value=v, inline=True)
    return embed


async def post_a_question():
    channel = bot.get_channel(postdaily['channelid'])
    with DB() as db:
        qdata = db.get_ques(diff=postdaily['difficulty'], tag=None)
        if not qdata:
            async with channel.typing():
                channel.send("Something Went Wrong. Trouble sending a question")
            return

        if qdata['source'] == 'LC':
            embed = make_embed_lc(qdata, handle_lc(qdata))
        else:
            embed = make_embed_cf(qdata, handle_cf(qdata))

        db.after_posted(qdata['id'])
        async with channel.typing():
            await channel.send(f"Question for the day: ", embed=embed)


#######################################
#               TASKS                 #
#######################################


@tasks.loop(hours=22.0)
async def post_a_question_task():
    await post_a_question()


@post_a_question.after_loop
async def pin_new_message():
    try:
        channel = bot.get_channel(postdaily['channelid'])
        newm = await channel.history(limit=1).flatten()[0]
        if newm.author == bot.user:
            await newm.pin()
    except Exception as e:
        print(e)
        print(traceback.format_exc())


@post_a_question.before_loop
async def unpin_old_message():
    try:
        channel = bot.get_channel(postdaily['channelid'])
        oldm = await channel.history(limit=1).flatten()[0]
        if oldm.author == bot.user:
            await oldm.unpin()
    except Exception as e:
        print(e)
        print(traceback.format_exc())


bot.run(os.environ.get('DC_BOT_TOKEN', None))  # bot token in environment variable DC_BOT_TOKEN
