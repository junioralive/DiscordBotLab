# NOTE: RUN THIS SCRIPT IN LOCAL SYSTEM

import discord
import os
import tkinter as tk
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
import time
import logging

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

TOKEN = 'PUT TOKEN ID HERE'

class ScreenshotHandler(FileSystemEventHandler):
    def __init__(self, channel, loop):
        self.channel = channel
        self.loop = loop

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.png'):
            if not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self.send_screenshot(event.src_path), self.loop)
            else:
                logging.error("Event loop is closed, cannot send screenshot")

    async def send_screenshot(self, path):
        await asyncio.sleep(1)
        timeout = 10
        start_time = time.time()

        while os.path.getsize(path) == 0 and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)
            logging.info("Waiting for file to be written...")

        if os.path.getsize(path) > 0:
            logging.info("Sending screenshot...")
            message = await self.channel.send(file=discord.File(path))
            print("Screenshot sent to Discord channel.")

            def check(m):
                return m.reference and m.reference.message_id == message.id

            try:
                reply = await client.wait_for('message', check=check, timeout=60)
                filter_reply = reply.content.replace("```", "")
                print(filter_reply)
                Thread(target=create_transparent_window, args=(filter_reply,)).start()
                
            except asyncio.TimeoutError:
                logging.warning("No reply received within 60 seconds.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
        else:
            logging.warning("File is still empty after waiting, not sending.")

def create_transparent_window(message):
    root = tk.Tk()
    root.withdraw()
    top = tk.Toplevel(root)
    top.attributes('-alpha', 0.2)
    top.wm_attributes("-transparentcolor", "white")
    top.attributes('-topmost', True)
    top.overrideredirect(True)
    max_width = 1920
    #max_height = 1080
    window_width = 400
    window_height = 100
    position_right = (max_width - window_width) // 2
    position_bottom = 920
    top.geometry(f"{window_width}x{window_height}+{position_right}+{position_bottom}")
    #label = tk.Label(top, text=message, font=('Helvetica', '16'), fg='black', bg='white', highlightthickness=1, highlightbackground='white')
    label = tk.Label(top, text=message, font=('Helvetica', '16'), fg='black', bg='white')
    label.pack(fill='both', expand=True)
    top.after(1000, top.destroy)
    root.mainloop()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel("PUT CHANNEL ID HERE")
    if channel is None:
        print("Channel not found. Please verify the channel ID.")
        return

    folder_path = r"C:\Users\theju\Pictures\Screenshots"
    loop = asyncio.get_running_loop()
    event_handler = ScreenshotHandler(channel, loop)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()

    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

client.run(TOKEN)