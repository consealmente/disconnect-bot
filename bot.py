import asyncio
import json
from urllib.parse import urlencode
import getpass
import logging
import os
import re
import sqlite3
from pathlib import Path

import discord
from discord import app_commands

db = sqlite3.connect(Path(__file__).with_name("rules.sqlite3"))
db.execute("CREATE TABLE IF NOT EXISTS rules (guild TEXT PRIMARY KEY, target TEXT, trigger TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS dashboard_versions (guild TEXT PRIMARY KEY, version INTEGER NOT NULL)")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://disconnect-bot-death16.vercel.app").rstrip("/")


def version(guild):
    row = db.execute("SELECT version FROM dashboard_versions WHERE guild=?", (guild,)).fetchone()
    return row[0] if row else 0


def save(guild, trigger, targets):
    with db:
        db.execute("INSERT OR REPLACE INTO dashboard_versions VALUES (?, ?)", (guild, version(guild) + 1))
        if targets:
            db.execute("INSERT OR REPLACE INTO rules VALUES (?, ?, ?)", (guild, ",".join(targets), trigger))
        else:
            db.execute("DELETE FROM rules WHERE guild=?", (guild,))


intents = discord.Intents.none()
intents.guilds = True
intents.voice_states = True


class VoiceBot(discord.Client):
    async def setup_hook(self):
        await commands.sync()


bot = VoiceBot(intents=intents)
commands = app_commands.CommandTree(bot)


def valid_id(value):
    return re.fullmatch(r"[1-9][0-9]{14,19}", value) and int(value) < 2**64


@commands.command(description="Choose who gets disconnected when someone joins their voice channel.")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(target_id="Member ID to disconnect", trigger_id="Joining member ID; leave blank for any other member")
async def voice_rule(interaction: discord.Interaction, target_id: str, trigger_id: str | None = None):
    if not valid_id(target_id) or (trigger_id is not None and not valid_id(trigger_id)):
        return await interaction.response.send_message("Paste a numeric Discord user ID in each ID field.", ephemeral=True)
    if target_id == trigger_id:
        return await interaction.response.send_message("Choose two different members.", ephemeral=True)
    save(str(interaction.guild_id), trigger_id, [target_id])
    who = f"<@{trigger_id}>" if trigger_id else "any other member"
    await interaction.response.send_message(f"Saved. When {who} joins the channel occupied by <@{target_id}>, I’ll disconnect <@{target_id}>.", ephemeral=True)


@commands.command(description="Turn off automatic voice disconnects for this server.")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def voice_off(interaction: discord.Interaction):
    save(str(interaction.guild_id), None, [])
    await interaction.response.send_message("Automatic disconnects are off.", ephemeral=True)


@commands.error
async def command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Only server administrators can change this rule.", ephemeral=True)
    else:
        logging.error("Slash command failed", exc_info=error)
        if not interaction.response.is_done():
            await interaction.response.send_message("Command failed. Check the bot console.", ephemeral=True)


@bot.event
async def on_voice_state_update(member, before, after):
    channel = after.channel
    if channel is None or before.channel == channel:
        return
    rule = db.execute("SELECT target, trigger FROM rules WHERE guild = ?", (str(member.guild.id),)).fetchone()
    if not rule:
        return
    target_id, trigger_id = rule
    if trigger_id and str(member.id) != trigger_id:
        return

    async def disconnect(raw_id):
        target = member.guild.get_member(int(raw_id))
        if target is None or target == member or not target.voice or target.voice.channel != channel:
            return
        try:
            await target.move_to(None, reason=f"Voice rule triggered by member {member.id}")
        except discord.HTTPException as error:
            logging.warning("Disconnect failed for %s in channel %s: %s", raw_id, channel.id, error)

    if member.voice and member.voice.channel == channel:
        await asyncio.gather(*(disconnect(raw_id) for raw_id in target_id.split(",")))


@commands.command(description="Open the private voice rule dashboard.")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def dashboard(interaction: discord.Interaction):
    guild = str(interaction.guild_id)
    revision = version(guild)
    rule = db.execute("SELECT trigger,target FROM rules WHERE guild=?", (guild,)).fetchone()
    initial = {"state": "open", "trigger": (rule[0] or "") if rule else "", "targets": rule[1].split(",") if rule else []}
    link = DASHBOARD_URL + "/#" + urlencode({"app": interaction.application_id, "session": interaction.token})
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Open private dashboard", url=link))
    await interaction.response.send_message(json.dumps(initial, separators=(",", ":")), ephemeral=True, view=view)
    # Fetch a fresh copy on each poll; original_response() caches its first result.
    for _ in range(165):
        await asyncio.sleep(5)
        try:
            message = await interaction.followup.fetch_message("@original")
        except discord.NotFound:
            return
        except discord.HTTPException:
            continue
        try:
            edit = json.loads(message.content)
            if edit.get("state") != "pending":
                continue
            targets = list(dict.fromkeys(edit["targets"]))
            trigger = edit["trigger"]
            if len(targets) > 75 or any(not valid_id(item) for item in targets):
                raise ValueError
            if targets and (not valid_id(trigger) or trigger in targets):
                raise ValueError
            if version(guild) != revision:
                result = "Rule changed since opening. Run /dashboard again."
            else:
                save(guild, trigger, targets)
                result = "Rule saved." if targets else "Rule disabled."
        except (AttributeError, TypeError, KeyError, ValueError):
            result = "Invalid rule. Open a new dashboard."
        await interaction.edit_original_response(content=json.dumps({"state":"done","message":result}), view=None)
        return
    await interaction.edit_original_response(content='{"state":"done","message":"Session expired. Run /dashboard again."}', view=None)


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN") or getpass.getpass("Paste bot token (hidden) and press Enter: ")
    bot.run(token.strip())
