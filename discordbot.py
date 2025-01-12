import discord
import requests
import json
import os 

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready() -> None:
    print(f"Logged In As {bot.user}")

SUPPORTED_RUNTIMES = {}

def get_language_version(language):
    global SUPPORTED_RUNTIMES
    if not SUPPORTED_RUNTIMES:
        response = requests.get("https://emkc.org/api/v2/piston/runtimes")
        if response.status_code == 200:
            SUPPORTED_RUNTIMES = {runtime["language"]: runtime["version"] for runtime in response.json()}
    return SUPPORTED_RUNTIMES.get(language, None)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"Received a message from {message.author}: {message.content}")
    await bot.process_commands(message)

@bot.command()
async def compile(ctx, language: str) -> None:
    if not ctx.message.attachments:
        await ctx.send("Please attach a markdown file with the code to compile.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(".md"):
        await ctx.send("Please provide a valid markdown file.")

    try:
        content = await attachment.read()
        content = content.decode("utf-8")
        
        if f"```{language}" not in content:
            await ctx.send(f"Could not find a code block in the provided language.")
            return
        codeBlock = content.split(f"```{language}")[1].split("```")[0].strip()
        version = get_language_version(language)
        if not version:
            await ctx.send(f"Language '{language}' is not supported.")
            return

        api_url = "https://emkc.org/api/v2/piston/execute"
        payload = {
            "language": language,
            "version": version,  
            "files": [
                {
                    "name": "main.md",  
                    "content": codeBlock 
                }
            ]
        }
        header = {
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, data=json.dumps(payload), headers=header)
        print(response.json())
        if response.status_code == 200:
            result = response.json()
            output = result["run"]["output"]
            await ctx.send(f"Output: \n```\n{output}\n```")
        else:
            await ctx.send(f"An error occured during compilation: {response.text}")
    except Exception as Error:
        await ctx.send(f"An error occured: {Error}")


bot.run(os.getenv("BOT_TOKEN"))