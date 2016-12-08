import random
import discord
from time import sleep
import youtube_dl
import re
bot = discord.Client()
voice_bots = {}
owner = "Shubidubapp"   # Yes. Bot does listen to my commands in any case. I'm his father ofc he does that.
opts = {
    'default_search': 'auto',
    'quiet': True,
}
tts_file_name = "tts_commands.txt"
keywords = ["!here", "!clean", "!join", "!move"]
tts_keywords = []

def import_token():
    token = open("token.txt").readline().strip()
    return token

async def message_delete(message):
    try:
        if message is not None:
            await bot.delete_message(message)
    except discord.NotFound:
        pass


class MusicPlayer:
    voice_bot = None
    ch = None
    playlist = []
    volume = 0.2
    player = None
    server_name = None
    wait = True
    first_time = True

    async def add(self, url, message):
        await message_delete(message)
        if self.player is None:
            if self.voice_bot is None:
                self.voice_bot = await bot.join_voice_channel(self.ch)
            try:
                self.player = await self.voice_bot.create_ytdl_player(url, ytdl_options=opts)
            except youtube_dl.DownloadError:
                await bot.send_message(message.channel, "%%s This is not a valid URL" % message.author.name)
                return
            self.player.volume = self.volume
            self.player.start()
            sec = self.player.duration % 60
            minute = int((self.player.duration - sec) / 60)
            duration = "%02d.%02d" % (minute, sec)
            await bot.send_message(message.channel, "%s started playing the song :" % message.author.name)
            await bot.send_message(message.channel, "%s \t Duration: %s" % (self.player.title, duration))
        elif self.player.is_playing():
            self.playlist.append([url, message])
            await bot.send_message(message.channel, "%s added a song to the queue." % message.author.name)
            await bot.send_message(message.channel, "The song is %s. song in the queue" % len(self.playlist))

    async def change_volume(self, volume, message):
        if self.player is not None:
            self.player.volume = volume / 100
            await bot.send_message(message.channel, "%s changed volume to: %s" % (message.author.name, volume))
        else:
            await bot.send_message(message.channel, "%s, There is no song playing" % message.author.name)
        await message_delete(message)

    async def stop(self, message):
        await message_delete(message)
        if self.voice_bot is not None:
            if self.player is not None:
                self.player.stop()
                self.playlist = []
                self.player = None
            if message is not None:
                await bot.send_message(message.channel, "%s stopped the party!" % message.author.name)
            await self.voice_bot.disconnect()
            self.voice_bot = None

        else:
            await bot.send_message(message.channel, "%s, There is no song playing" % message.author.name)

    async def next_song(self, message):
        await message_delete(message)
        url_list = self.playlist.pop(0)
        url, author = url_list[0], url_list[1].author
        self.wait = True
        # await self.player.stop()
        self.player.stop()
        self.player = await self.voice_bot.create_ytdl_player(url, ytdl_options=opts)
        channel = url_list[1].channel
        sec = self.player.duration % 60
        minute = int((self.player.duration - sec) / 60)
        duration = "%02d.%02d" % (minute, sec)
        await bot.send_message(channel, "%s skipped a song." % message.author.name)
        await bot.send_message(channel, "Playing the song from playlist added by %s :" % author.name)
        await bot.send_message(channel, "%s \t Duration: %s" % (self.player.title, duration))
        sleep(1)
        self.player.start()

    async def auto_next(self):
        url_list = self.playlist.pop(0)
        url, author = url_list[0], url_list[1].author
        self.wait = True
        await self.player.stop()
        self.player = await self.voice_bot.create_ytdl_player(url, ytdl_options=opts)
        channel = url_list[1].channel
        sec = self.player.duration % 60
        minute = int((self.player.duration - sec) / 60)
        duration = "%02d.%02d" % (minute, sec)
        await bot.send_message(channel, "Playing the song from playlist added by %s :" % author.name)
        await bot.send_message(channel, "%s \t Duration: %s" % (self.player.title, duration))
        sleep(1)
        self.player.start()

    async def player_loop(self):
        self.wait = False
        while self.player.is_playing() or len(self.playlist) != 0:
            if self.wait:
                return
            if not self.player.is_playing():
                await self.auto_next()
            sleep(3)
        await self.stop(None)
        return None

    async def handle_music(self, message):
        msg_split = message.content.split(" ", 2)
        if len(msg_split) >= 2:
            cmd = msg_split[1]
            if (cmd.lower() == "add" or cmd.lower() == "play") and len(msg_split) >= 3:
                await self.add(url=msg_split[2], message=message)
            elif cmd.lower() == "stop":
                await self.stop(message)
            elif cmd.lower() == "volume" and len(msg_split) == 3:
                await self.change_volume(int(msg_split[2]), message)
            elif cmd.lower() == "next":
                await self.next_song(message)
            else:
                if cmd.startswith("https://www.youtube.com/"):
                    await self.add(msg_split[1], message)
                else:
                    await message_delete(message)
                    await bot.send_message(message.channel, "U wot m8? (╯°□°）╯︵ ┻━┻")
        if self.wait and self.first_time:
            self.first_time = False
            await bot.loop.create_task(self.player_loop())


def create(message):
    mplayer = MusicPlayer()
    mplayer.ch = message.author.voice.voice_channel
    mplayer.server_name = message.server.name
    voice_bots[mplayer.server_name] = mplayer
    return mplayer


async def no_perm(message):
    author = message.author
    channel = message.channel
    await bot.send_message(channel, "Hey %s !! You ain't got permission for that move smartpants" % author.name)


async def join(message):
    invite_link = "https://discordapp.com/oauth2/authorize?client_id=233968062301208586&scope=bot&permissions=0"
    msg = await bot.send_message(message.channel, invite_link)
    sleep(10)
    await message_delete(msg)

async def clean_channel(message):
    channel = message.channel
    author = message.author
    msgs = message.content.split(" ")
    count = -1
    pin = False
    if len(msgs) >= 2:
        try:
            msgs[1] = int(msgs[1])
        except ValueError:
            pass
        if type(msgs[1]) == int and msgs[1] >= 0:
            count = msgs[1]
        else:
            await bot.send_message(channel, "Hey %s." % author.name)
            await bot.send_message(channel, "Are you sure you wrote an integer between 0 and infinity ?")
            await bot.send_message(channel, "Well. Kind of infinity ¯\_(ツ)_/¯")
            return
    last_count = 0
    author_can_do_this = channel.permissions_for(author).manage_messages
    if author_can_do_this or author.name == owner:
        print("%s messages will be deleted, pin deleting is %s" % (count, str(pin)))
        delete_count = 0
        while True:
            messages_to_delete = []
            async for mmessage in bot.logs_from(channel, before=message):
                if mmessage.pinned:
                    continue
                else:
                    if count >= 1 or count <= -1:
                        count -= 1
                        messages_to_delete.append(mmessage)
                    elif count == 0:
                        break
            delete_count += len(messages_to_delete)
            print(count, "\t:\t", last_count)
            if len(messages_to_delete) == 1:
                await message_delete(messages_to_delete[0])
            elif len(messages_to_delete) >= 2:
                await bot.delete_messages(messages_to_delete)
            if count == 0 or last_count == count:
                break

            last_count = count
        await bot.delete_message(message)
        await bot.send_message(channel, "%s messages have been deleted. By %s" % (delete_count, author.name))
        return

    else:
        await no_perm(message)


async def move_everyone_to_channel(message):  # expected message.content = !move channel_name, name1 name2...
    print(message.content)
    cmd_split = message.content.replace("!move ", "").split(", ")
    channel_to_move = cmd_split[0]
    print(cmd_split)
    try:
        not_included_users = cmd_split[1].split(" ")    # name1, name2 are optional, this puts them in a list if given
    except IndexError:
        not_included_users = []
    voice_channel_list = message.server.channels
    for ch in voice_channel_list:   # Finds the given channel_name
        if (channel_to_move.lower() in ch.name.lower()) and ch.type == discord.ChannelType.voice:
            channel_to_move = ch
            break
    else:
        await bot.send_message(message.channel, "The said channel doesn't exist or It's not a voice channel")
        await message_delete(message)
        return
    channel_to_move_from = message.author.voice.voice_channel
    if channel_to_move_from is None:    # Checking if the message.author in a voice channel
        await bot.send_message(message.channel, "%s, You should be in a voice channel to use this command."
                               % message.author.name)
        await message_delete(message)
        return

    channel_members = channel_to_move_from.voice_members    # Gets the channel members
    if channel_to_move == channel_to_move_from:
        await bot.send_message(message.channel, "You're already at %s, %s" % (channel_to_move.name,
                                                                              message.author.name))
        await message_delete(message)
        return
    print(channel_to_move_from, "\t-->\t", channel_to_move)
    author_can_do_this1 = channel_to_move_from.permissions_for(message.author).move_members
    author_can_do_this2 = channel_to_move.permissions_for(message.author).move_members
    author_can_do_this3 = (author_can_do_this1 and author_can_do_this2) or message.author.name == owner
    if not author_can_do_this3:
        await no_perm(message)
        return
    ni_string = ""
    ni_users_for_print = []
    copied_members = channel_members.copy()
    not_included_users_copy = not_included_users.copy()
    for user in copied_members:    # Removes the name1 name2 etc if given from the channel members
        for ni_user in not_included_users_copy:
            if user.name.lower().startswith(ni_user.lower()):
                ni_users_for_print.append(user.name)
                not_included_users_copy.remove(ni_user)
                copied_members.remove(user)
                break
    if len(ni_users_for_print) != 0:
        ni_string = " except "
        ni_string += ", ".join(ni_users_for_print)
    for user in copied_members:
        await bot.move_member(user, channel_to_move)
    move_msg = "%s moved everyone %s from %s to %s" % (message.author.name, ni_string,
                                                       channel_to_move_from.name, channel_to_move.name)
    await bot.send_message(message.channel, move_msg)
    await message_delete(message)

async def tts_command_add(message):
    if message.channel.permissions_for(bot.user).send_tts_messages() and \
            message.channel.permissions_for(message.author).send_tts_messages():
        msg = message.content.replace("!learn", "")
        keyword = msg.split(" ", 1)[0][1:]
        tts_message = msg(" ", 1)[1].strip()
        if keyword not in keywords and keyword not in tts_keywords:
            tts_file = open(tts_file_name, "a")
            tts_file.write("%s %s\n" % (keyword, tts_message))
            tts_keywords.append(keyword)
            tts_file.close()
            await bot.send_message(message.channel, "%s taught me %s" % (message.author, keyword))
        else:
            await bot.send_message(message.channel, "%s, you can't use this keyword." % message.author)
    else:
        await bot.send_message(message.channel,
                               "%s, one of us doesn't have permission to send TTS Messages in this channel")


async def tts_command_remove(message):
    if message.channel.permissions_for(message.author).administrator:
        msg = message.content.replace("!remove ", "")
        keyword = msg.split(" ", 1)[0]
        if keyword in keywords:
            tts_file = open(tts_file_name)
            lines = tts_file.readlines()
            tts_file.close()
            tts_file = open(tts_file_name, "w")
            for line in lines:
                tts_keyword = line.split(" ", 1)[0][1:]
                if keyword != tts_keyword:
                    tts_file.write(line)
            keywords.remove(keyword)


async def tts_learned_so_far(message):
    output = ", ".join(tts_keywords)
    await bot.send_message(message.author, "I know these: %s" % output)


async def tts_command_send(message):
    if message.channel.permissions_for(bot.user).send_tts_messages() and \
            message.channel.permissions_for(message.author).send_tts_messages():
        keyword = message.content.replace("!", "")
        if keyword in keywords:
            tts_file = open(tts_file_name, "r")
            lines = tts_file.readlines()
            for line in lines:
                pre_saved_keyword = line.split(" ", 1)[0]
                if keyword == pre_saved_keyword:
                    tts_message = line.split(" ", 1)[1]
                    await bot.send_message(message.channel, "%s says:%s" % (message.author, tts_message), tts=True)
            tts_file.close()


@bot.event
async def on_ready():
    bot.wait_until_login()
    with open(tts_file_name, "r") as tts_file:
        lines = tts_file.readlines()
        for line in lines:
            line = line.strip()
            tts_keywords.append(line.split(" ", 1)[0])


@bot.event
async def on_message(message):
    if message.author != bot.user:
        if message.content.startswith("!here"):
            await bot.delete_message(message)
            await bot.send_message(message.channel, "I am, The Great %s-sama, here. ┬─┬﻿ ノ( ゜-゜ノ)" % bot.user.name)
        elif message.content.startswith("!join "):
            join(message)
        elif message.content.startswith("!clean") or message.content.startswith("!clear"):
            await clean_channel(message)
        # elif message.content.startswith("!music "):
        #     if message.server.name in voice_bots.keys():
        #         mplayer = voice_bots[message.server.name]
        #     else:
        #         mplayer = create(message)
        #     print(mplayer)
        #     await mplayer.handle_music(message)
        #     if mplayer.voice_bot is None:
        #         voice_bots.pop(message.server.name)
        elif message.content[0] in "*-+'.," or "niyazi" in message.content.lower():
            rnd_choice = random.choice([0, 1, 2, 3])
            if rnd_choice == 3:
                await bot.send_message(message.channel, "Niyazi !!! My Greatest nemesis. BURN HIM!!!! (╯°□°）╯︵ ┻━┻")
        elif message.content.startswith("!move"):
            await move_everyone_to_channel(message)
        elif "fuck" in message.content:
            rnd_choice = random.choice([0, 1, 2, 3])
            bot.counter += 1
            if rnd_choice >= 2 or bot.counter == 4:
                bot.counter = 0
                await bot.send_message(message.channel, "No! FUCK YOU (╯°□°）╯︵ ┻━┻")
        elif message.content.startswith("!learn"):
            tts_command_add(message)
        elif message.content.startswith("!remove"):
            tts_command_remove(message)
        elif message.content.startswith("!magicwords"):
            tts_learned_so_far(message)
        elif message.content.replace("!", "").strip() in keywords:
            tts_command_send(message)


bot.counter = 0
bot.run(import_token())
bot.close()
