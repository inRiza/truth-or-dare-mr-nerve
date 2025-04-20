from discord import Client, Intents
import random
import os
import sqlite3
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

intents = Intents.default()
intents.message_content = True

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        print("Warning: GOOGLE_API_KEY not found in environment variables. Roast feature will not work.")
        GEMINI_AVAILABLE = False
except ImportError:
    print("Warning: google-generativeai package not installed. Roast feature will not work.")
    GEMINI_AVAILABLE = False
except Exception as e:
    print(f"Error configuring Google Generative AI: {e}")
    GEMINI_AVAILABLE = False

def init_db():
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute("CREATE TABLE IF NOT EXISTS truths (id INTEGER PRIMARY KEY, content TEXT NOT NULL)")
  c.execute("CREATE TABLE IF NOT EXISTS dares (id INTEGER PRIMARY KEY, content TEXT NOT NULL)")
  conn.commit()
  conn.close()
    
init_db()

# get a random entry from the database
# and return it
def get_random_entry(table):
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute(f"SELECT content FROM {table} ORDER BY RANDOM() LIMIT 1")
  entries = c.fetchall()
  conn.close()
  return random.choice(entries)[0] if entries else None

# add a new entry to the database
def add_entry(table, content):
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute(f"INSERT INTO {table} (content) VALUES (?)", (content,))
  conn.commit()
  conn.close()
  
def delete_all_entries(table):
  conn = sqlite3.connect('truthordare.db')
  c = conn.cursor()
  c.execute(f"DELETE FROM {table}")
  conn.commit()
  conn.close()

def delete_all_truths():
  delete_all_entries('truths')

def delete_all_dares():
  delete_all_entries('dares')
  
# Gemini-powered roast generation
async def generate_gemini_roast(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        full_prompt = f"""You are a mean and savage AI. Create a roast that could anger people.
        The person said: "{prompt}"
        
        Create a short, witty, and cutting roast based on this. Be creative and personal.
        Keep it under 100 characters and make it funny but mean."""
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=100,
            temperature=0.9
        )
        
        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config=generation_config
        )
        
        if not response.text:
            return "Sorry, I couldn't generate a roast for that. Try something else!"
            
        return response.text.strip()
    except Exception as e:
        print(f"Error generating roast with Gemini: {str(e)}")
        return "Sorry, I encountered an error while generating a roast. Please try again later."

# Main roast generation function that uses Gemini
async def generate_roast_caption(prompt):
    if GEMINI_AVAILABLE:
        return await generate_gemini_roast(prompt)
    else:
        return "Sorry, the roast feature is currently unavailable. Please check back later."

class MyClient(Client):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.admin_active = False
    self.roast_active = False
  
  async def on_ready(self):
    print('Logged on as {0}!'.format(self.user))
    
  async def on_message(self, message):
    if message.author == self.user:
      return

    content = message.content.lower()
    
    if content.startswith('/hello'):
      await message.channel.send('Hello! I am Mr. Nerve, your friendly Discord bot!')
      await message.channel.send('''Here are my commands:
/truth - Get a random truth
/dare - Get a random dare
/addtruth - Add a truth
/adddare - Add a dare
/roastmode - Activate roast mode''')
    
    elif content.startswith('/admin'):
      input_password = content[len('/admin '):].strip()
      if input_password != os.getenv("ADMIN_PASSWORD"):
        await message.channel.send('❌ Incorrect password!')
        return
      await message.channel.send('✅ Admin mode activated!')
      self.admin_active = True
      await message.channel.send('''Hello Admin! What do you want to do?
/deleteall - Delete all truths and dares
/deletealltruth - Delete all truths
/deletealldare - Delete all dares
/showtruths - Show all truths
/showdares - Show all dares''')
      
    elif self.admin_active:
      if content.startswith('/deleteall'):
        delete_all_truths()
        delete_all_dares()
        await message.channel.send('✅ All truths and dares deleted!')
        
      elif content.startswith('/deletealltruth'):
        delete_all_truths()
        await message.channel.send('✅ All truths deleted!')
      
      elif content.startswith('/deletealldare'):
        delete_all_dares()
        await message.channel.send('✅ All dares deleted!')
      
      elif content.startswith('/showtruths'):
        await message.channel.send('Here are all the truths:')
        conn = sqlite3.connect('truthordare.db')
        c = conn.cursor()
        c.execute("SELECT content FROM truths")
        truths = c.fetchall()
        conn.close()
        if truths:
          for truth in truths:
            await message.channel.send(truth[0])
        else:
          await message.channel.send('No truths found.')
        
      elif content.startswith('/showdares'):
        await message.channel.send('Here are all the dares:')
        conn = sqlite3.connect('truthordare.db')
        c = conn.cursor()
        c.execute("SELECT content FROM dares")
        dares = c.fetchall()
        conn.close()
        if dares:
          for dare in dares:
            await message.channel.send(dare[0])
        else:
          await message.channel.send('No dares found.')
      
    elif content.startswith('/roastmode'):
      await message.channel.send('Roast mode activated!')
      self.roast_active = True
    
    elif content.startswith('/truth'):
      truth = get_random_entry('truths')
      await message.channel.send(truth)
      if self.roast_active:
        roast_prompt = await generate_roast_caption(truth)
        await message.channel.send(roast_prompt)

    
    elif content.startswith('/dare'):
      dare = get_random_entry('dares')
      await message.channel.send(dare)
      
    elif content.startswith('/addtruth'):
      add_truth = content[len('/addtruth '):].strip()
      if add_truth:
        add_entry('truths', add_truth)
        await message.channel.send('✅ Truth added!')
      else:
        await message.channel.send('❌ Please provide a truth to add.')
      
    elif content.startswith('/adddare'):
      add_dare = content[len('/adddare '):].strip()
      if add_dare:
        add_entry('dares', add_dare)
        await message.channel.send('✅ Dare added!')
      else:
        await message.channel.send('❌ Please provide a dare to add.')

# Create and run the client
client = MyClient(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
