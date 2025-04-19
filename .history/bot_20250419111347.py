from discord import Client, Intents
import random
import os
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()


def init_db():
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute("CREATE TABLE IF NOT EXIST truths (id INTEGER PRIMARY KEY, content TEXT NOT NULL)")
  c.execute("CREATE TABLE IF NOT EXIST dares (id INTEGER PRIMARY KEY, content TEXT NOT NULL)")
  conn.commit()
  conn.close()
    
init_db()

def get_random_entry(table):
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute(f"SELECT content FROM {table} ORDER BY RANDOM() LIMIT 1")
  entries = c.fetchall()
  conn.close()
  return random.choice(entries)[0] if entries else None

def add_entry(table, content):
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute(f"INSERT INTO {table} (content) VALUES (?)", (content,))
  conn.commit()
  conn.close()
  
class MyClient(Client):
  async def on_ready(self):
    print('Logged on as {0}!'.format(self.user))
    
  async def on_message(self, message):
    if message.author == self.user:
      return

    content = message.content.lower()
    
    if content.startswith('/hello'):
      await message.channel.send('Hello World!')
      
    elif content.startswith('/truth'):
      truth = get_random_entry('truths')
      await message.channel.send(truth)
    
    elif content.startswith('/dare'):
      dare = get_random_entry('dares')
      await message.channel.send(dare)
      
    elif content.startswith('/addtruth'):
      add_truth = content[len('/addtruth '):].strip()
      if add_truth:
        add_entry('truths', add_truth)
        await message.channel.send(f'✅ Truth added!')
      else:
        await message.channel.send('❌ Please provide a truth to add.')
      
    elif content.startswith('/adddare'):
      add_dare = content[len('/adddare '):].strip()
      if add_dare:
        add_entry('dares', add_dare)
        await message.channel.send(f'✅ Dare added!')
      else:
        await message.channel.send('❌ Please provide a dare to add.')
    

intents = Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
