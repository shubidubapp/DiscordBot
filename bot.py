import random
import discord
from time import sleep
import youtube_dl
bot = discord.Client()
voice_bots = {}
owner = "Shubidubapp"   # Yes. Bot does listen to my commands in any case. I'm his father ofc he does that.
opts = {
    'default_search': 'auto',
    'quiet': True,
}
def import_token():
    token = open("token.txt").readline().strip()
    return token

async def message_delete(message):
    if message is not None:
        await bot.delete_message(message)


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
                print("created voice_bot")
                self.voice_bot = await bot.join_voice_channel(self.ch)
            try:
                print("Created player")
                self.player = await self.voice_bot.create_ytdl_player(url, ytdl_options=opts)
            except youtube_dl.DownloadError:
                print("Got an error body")
                await bot.send_message(message.channel, "%%s This is not a valid URL" % message.author.name)
                return
            self.player.volume = self.volume
            self.player.start()
            print("Started player")
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
        print(self.player)
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
            print("loop loop loop loop")
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
            print(message.content)
            if (cmd.lower() == "add" or cmd.lower() == "play") and len(msg_split) >= 3:
                print("Command is play/add")
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
        messages_to_delete = []
        while True:
            async for mmessage in bot.logs_from(channel, before=message):
                if mmessage.pinned:
                    continue
                else:
                    if count == 0:
                        break
                    else:
                        count -= 1
                        messages_to_delete.append(mmessage)
            await bot.delete_messages(messages_to_delete)
            if count == 0 or last_count == count:
                break
            last_count = count
        await bot.delete_message(message)
        return

    else:
        await no_perm(message)


async def move_everyone_to_channel(message):  # expected message.content = !move channel_name, name1 name2...
    cmd_split = message.content.strip("!move ").split(", ")
    channel_to_move = cmd_split[0]
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
        return
    channel_to_move_from = message.author.voice.voice_channel
    if channel_to_move_from is None:    # Checking if the message.author in a voice channel
        await bot.send_message(message.channel, "%s, You should be in a voice channel to use this command."
                               % message.author.name)
        return

    channel_members = channel_to_move_from.voice_members    # Gets the channel members
    author_can_do_this1 = channel_to_move_from.permissions_for(message.author).move_members
    author_can_do_this2 = channel_to_move.permissions_for(message.author).move_members
    author_can_do_this3 = (author_can_do_this1 and author_can_do_this2) or message.author == owner
    if author_can_do_this3:
        await no_perm(message)
        return
    for user in channel_members:    # Removes the name1 name2 etc if given from the channel members
        for ni_user in not_included_users:
            if user.name.lower().startswith(ni_user.lower()):
                not_included_users.remove(ni_user)
                channel_members.remove(user)
                break
    copy = channel_members.copy()
    for user in copy:
        await bot.move_member(user, channel_to_move)

    await message_delete(message)


@bot.event
async def on_ready():
    bot.wait_until_login()
    print("I am, The Great %s-sama, here." % bot.user.name)


@bot.event
async def on_message(message):
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
        print(rnd_choice)
        if rnd_choice == 3:
            await bot.send_message(message.channel, "Niyazi !!! My Greatest nemesis. BURN HIM!!!! (╯°□°）╯︵ ┻━┻")
    elif message.content.startswith("!move"):
        await move_everyone_to_channel(message)


bot.run(import_token())
bot.close()
