import discord
from discord.ext import commands
from discord import EventStatus
from discord.ui import Button, View

import time
import datetime

import asyncio

import gspread
from google.oauth2.service_account import Credentials

# Set up intents
intents = discord.Intents.default()
intents.guild_scheduled_events = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="đ", intents=intents)


SERVICE_ACCOUNT_FILE = "BotCreds.json"
SPREADSHEET_ID = "1Q8x4Qa9_8k7RpjqVnojw-BDeOeTEq1gnhYmrQdvqIr4"

MaxLine = 30 #default = 30
MinTime = 15 #default = 15
WaitForCoHost = 60 #default = 60

is_timer_running = False
members_in_vc = {}
guild_id = 611454267965964290 
ReportChannelID = 802613614469054504
TrackedVoiceChannelID = 1117281625647099924
BotToken = "MTI5NDQ4MzE0Njc2MjYxNjg1NA.GckgDk.d2IJsTsCUm-HyMVb2zSELVIodGwktbsk7vzik8"

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Import")

gamenight_message = None

""" Carbon Meister Official Server IDs

guild_id = 611454267965964290 
ReportChannelID = 802613614469054504
TrackedVoiceChannelID = 1117281625647099924
BotToken = "MTI5NDQ4MzE0Njc2MjYxNjg1NA.GckgDk.d2IJsTsCUm-HyMVb2zSELVIodGwktbsk7vzik8"

"""


""" Test Server IDs

guild_id = 708390420945567825 
ReportChannelID = 1292176893738614856
TrackedVoiceChannelID = 1300575898420117576
BotToken = "MTEyMDg1ODM5MDUwODM0NzQ3NA.G-gZ4C.2kQ-JUR6Pg1JxQDUZle3q7Gh6_8KUvFh2g6X-o"

"""


start_time = None
end_time = None
cohost = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

"""
# Override the on_message event to prevent command processing
@bot.event
async def on_message(message):

    if message.author == bot.user:
        return

    print(f"Received message: {message.content}")

    await bot.process_commands(message)
"""
@bot.event
async def on_scheduled_event_update(before, after):
    global is_timer_running, members_in_vc, start_time, end_time, cohost, gamenight_overview_message

    if before.status != after.status:
        guild = bot.get_guild(guild_id)
        if not guild:
            print(f"Unable to find the guild with ID {guild_id}")
            return
        
        channel = guild.get_channel(ReportChannelID)
        if not channel:
            print(f"Unable to find the channel with ID {ReportChannelID}")
            return

        host = after.creator if after.creator else None

        # Create embed1 here to avoid UnboundLocalError
        embed1 = discord.Embed()
        view = discord.ui.View(timeout=None)
        
        new_gamenight_info = None

        rounded_hours = 0
        unrounded_hours = 0
        rounded_minutes = 0
        unrounded_minutes = 0

        # Define buttons upfront
        join_button = discord.ui.Button(label="Join as CoHost", style=discord.ButtonStyle.primary)
        remove_button = discord.ui.Button(label="Remove CoHost", style=discord.ButtonStyle.danger)

        async def join_button_callback(interaction):
            if interaction.user.id == host.id:
                await interaction.response.send_message("You cannot assign yourself as the CoHost because you are the host!", ephemeral=True, delete_after=5)
                return

            global cohost
            cohost = interaction.user  # Assign the new cohost
            await interaction.response.send_message(f"CoHost assigned: {cohost.mention}", ephemeral=True, delete_after=5)

            if is_timer_running == True:
                new_gamenight_info = f"""
                ## Gamenight Overview:
                ### Name: `{after.name}`
                ### Host: {host.mention}
                ### CoHost: {cohost.mention}
                ### Duration: <a:Green:1335416471521857566> `Pending`
                ### Date: `{start_time.strftime('%Y-%m-%d')}`
                """
            else:
                new_gamenight_info = f"""
                ## Gamenight Overview:
                ### Name: `{after.name}`
                ### Host: {host.mention}
                ### CoHost: {cohost.mention}
                ### Duration: `{rounded_hours}h {rounded_minutes}m`
                ### Date: `{start_time.strftime('%Y-%m-%d')}`
                """

            embed1.description = new_gamenight_info
            embed1.set_image(url=after.cover_image.url if after.cover_image else None)

            # Rebuild the view to include buttons
            view = discord.ui.View(timeout=None)
            view.add_item(join_button)
            view.add_item(remove_button)
            await interaction.message.edit(embeds=[embed1], view=view)

        async def remove_button_callback(interaction):
            global cohost
            if cohost:
                await interaction.response.send_message(f"CoHost removed: {cohost.mention}", ephemeral=True, delete_after=5)
                cohost = None  # Remove cohost
            else:
                await interaction.response.send_message("No CoHost to remove!", ephemeral=True, delete_after=5)

            if is_timer_running == True:
                new_gamenight_info = f"""
                ## Gamenight Overview:
                ### Name: `{after.name}`
                ### Host: {host.mention}
                ### Duration: <a:Green:1335416471521857566> `Pending`
                ### Date: `{start_time.strftime('%Y-%m-%d')}`
                """
            else:
                new_gamenight_info = f"""
                ## Gamenight Overview:
                ### Name: `{after.name}`
                ### Host: {host.mention}
                ### Duration: `{rounded_hours}h {rounded_minutes}m`
                ### Date: `{start_time.strftime('%Y-%m-%d')}`
                """
                
            embed1.description = new_gamenight_info
            embed1.set_image(url=after.cover_image.url if after.cover_image else None)

            # Rebuild the view to include buttons
            view = discord.ui.View(timeout=None)
            view.add_item(join_button)
            view.add_item(remove_button)
            await interaction.message.edit(embeds=[embed1], view=view)

        # Assign callback functions to buttons
        join_button.callback = join_button_callback
        remove_button.callback = remove_button_callback

        # --- EVENT STARTED ---
        if after.status == EventStatus.active:
            start_time = datetime.datetime.now()
            is_timer_running = True
            members_in_vc = {}

            # Track members in the voice channel
            for member in guild.members:
                if member.voice and member.voice.channel:
                    members_in_vc[member.id] = [{
                        "start_time": discord.utils.utcnow().timestamp(),
                        "total_time": 0,
                    }]
            
            # Post "Gamenight Overview" at event start (without participants yet)
            GamenightInfoTable = f"""
            ## Gamenight Overview:
            ### Name: `{after.name}`
            ### Host: {host.mention}
            ### Duration: <a:Green:1335416471521857566> `Pending`
            ### Date: `{start_time.strftime('%Y-%m-%d')}`
            """

            embed1.description = GamenightInfoTable

            if after.cover_image:
                embed1.set_image(url=after.cover_image.url)

            # Add buttons to the view
            view.add_item(join_button)
            view.add_item(remove_button)

            # Send the Gamenight Overview and store message ID for later deletion
            gamenight_overview_message = await channel.send(embeds=[embed1], view=view)

        # --- EVENT ENDED ---
        elif after.status == EventStatus.completed:
            end_time = datetime.datetime.now()
            is_timer_running = False
            results_list = []

            # Update gamenight overview with the duration and participants
            for member_id, sessions in members_in_vc.items():
                member = await fetch_member(guild, member_id)
                total_time = sum(session["total_time"] for session in sessions)

                if member and member.voice and member.voice.channel:
                    last_session = sessions[-1]
                    total_time += discord.utils.utcnow().timestamp() - last_session["start_time"]

                total_minutes = int(total_time // 60)  # Store exact minutes for sheets
                if total_minutes < MinTime:
                    continue  

                unrounded_hours, unrounded_remainder = divmod(int(total_time), 3600)
                unrounded_minutes, _ = divmod(unrounded_remainder, 60)

                rounded_hours = unrounded_hours
                rounded_minutes = unrounded_minutes

                if rounded_minutes < MinTime:
                    rounded_minutes = 0
                elif MinTime <= rounded_minutes < 45:
                    rounded_minutes = 30
                elif 45 <= rounded_hours <= 59:
                    rounded_minutes = 0
                    rounded_hours += 1

                results_list.append({
                    "name": member.name if member else member.display_name if member else "Unknown Member", 
                    "actual_name": member.name if member else "Unknown Member",
                    "mention": member.mention if member else f"<@{member_id}>",
                    "id": member_id,
                    "time": f"{rounded_hours}h {rounded_minutes}m",
                    "unrounded_time": f"{unrounded_hours}h {unrounded_minutes}m",
                    "unrounded_minutes": total_minutes,
                })

            # Sort participants by name for the report
            results_list = sorted(results_list, key=lambda x: x["name"].lower())

            # Construct participant overview message
            participants_info = "\n".join([f"### {entry['mention']} (ID: `{entry['id']}`): `{entry['time']}`" for entry in results_list])
            embed = discord.Embed(
                title="Participants Overview",
                description=participants_info,
                color=discord.Color.blue()
            )

            # Update the gamenight overview with duration and participants
            new_gamenight_info = f"""
            ## Gamenight Overview:
            ### Name: `{after.name}`
            ### Host: {host.mention}
            ### CoHost: {cohost.mention if cohost else 'None'}
            ### Duration: `{rounded_hours}h {rounded_minutes}m`
            ### Date: `{start_time.strftime('%Y-%m-%d')}`
            """
            embed1.description = new_gamenight_info
            embed1.set_image(url=after.cover_image.url if after.cover_image else None)
            embed1.set_thumbnail(url="https://cdn.discordapp.com/attachments/1292176893738614856/1335751326558060605/EventFinished.png?ex=67a14edd&is=679ffd5d&hm=165deeed8a3900265ff24c13b475d4ab4abc43c18c67be83a8e64093a1fbdd82&")

            # Rebuild the view to include buttons
            view = discord.ui.View(timeout=None)
            view.add_item(join_button)
            view.add_item(remove_button)

            await gamenight_overview_message.edit(embeds=[embed1], view=view)
            await channel.send(embed=embed)

            await asyncio.sleep(WaitForCoHost)

            save_results_to_google_sheets(after, host, f"{unrounded_hours}h {unrounded_hours}m", end_time.strftime('%Y-%m-%d'), results_list, cohost)


def save_results_to_google_sheets(event, host, duration_str, end_date, results_list, cohost=None):
    duration_parts = duration_str.split('h')
    gamenight_hours = int(duration_parts[0].strip()) if duration_parts[0].strip() else 0
    gamenight_minutes = int(duration_parts[1].replace('m', '').strip()) if len(duration_parts) > 1 else 0
    total_gamenight_minutes = gamenight_hours * 60 + gamenight_minutes  # Convert to total minutes

    rows_for_gsheets = []

    for entry in results_list:
        participant_role = "Participant"
        if entry['id'] == host.id:
            participant_role = "Host"
        elif cohost and entry['id'] == cohost.id:
            participant_role = "CoHost"

        # Use unrounded time values for Google Sheets
        total_minutes = entry["unrounded_minutes"]

        row = [end_date, event.name, str(event.id), total_gamenight_minutes, participant_role, entry["actual_name"], str(entry["id"]), total_minutes]
        rows_for_gsheets.append(row)

    if rows_for_gsheets:
        rows_for_gsheets.sort(key=lambda x: x[5].lower())  # Sort by participant name (index 5)
        sheet.append_rows(rows_for_gsheets, value_input_option="RAW")
        print("Data successfully saved to Google Sheets (Import sheet).")
    else:
        print("No participant data to save.")


async def fetch_member(guild, member_id):
    member = guild.get_member(member_id)  # Try fetching from cache
    if not member:  
        try:
            member = await guild.fetch_member(member_id)  # Force fetch from API
        except discord.NotFound:
            return None  # Member not found
    return member

@bot.event
async def on_voice_state_update(member, before, after):
    global is_timer_running, members_in_vc

    if not is_timer_running:
        return

    member_id = member.id

    if after.channel and after.channel.id == TrackedVoiceChannelID and (not before.channel or before.channel.id != TrackedVoiceChannelID):
        if member_id not in members_in_vc:
            members_in_vc[member_id] = [{
                "start_time": time.time(),
                "total_time": 0,
            }]
        else:
            members_in_vc[member_id].append({
                "start_time": time.time(),
                "total_time": 0,
            })

        print(f"{member.name} joined the target VC.")

    if before.channel and before.channel.id == TrackedVoiceChannelID and (not after.channel or after.channel.id != TrackedVoiceChannelID):
        if member_id in members_in_vc:
            current_session = members_in_vc[member_id][-1]
            current_session["total_time"] += time.time() - current_session["start_time"]

            print(f"{member.name} left the target VC. Total time: {current_session['total_time']} seconds.")

'''
@bot.event
async def on_message(message):
    if message.author.id == 372048752229351434 and message.content.strip().lower() == "!perryinfo":
        await message.channel.send("Perry stinks extremely.")
    
    await bot.process_commands(message)
'''
bot.run(BotToken)