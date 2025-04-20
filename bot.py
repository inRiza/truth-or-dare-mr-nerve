from discord import Client, Intents
import random
import os
import sqlite3
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        print("Warning: GOOGLE_API_KEY not found in environment variables. Using local roast generation.")
        GEMINI_AVAILABLE = False
except ImportError:
    print("Warning: google-generativeai package not installed. Using local roast generation.")
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
  
# Local roast generation as fallback
def generate_local_roast(prompt):
    roast_templates = [
        "Oh, so you think {prompt}? That's the most ridiculous thing I've ever heard!",
        "Wow, {prompt}? You must be really desperate for attention.",
        "If you think {prompt}, you're even more delusional than I thought!",
        "Oh please, {prompt}? That's the best you can come up with?",
        "You actually believe {prompt}? That explains a lot about your personality.",
        "Only someone with zero self-awareness would say {prompt}.",
        "Is {prompt} supposed to impress someone? Because it's not working.",
        "You're really going with {prompt}? How original and boring.",
        "If {prompt} is your idea of interesting, I feel sorry for your friends.",
        "Oh look, another person who thinks {prompt}. How predictable."
    ]
    
    return random.choice(roast_templates).format(prompt=prompt)

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
            return generate_local_roast(prompt)
            
        return response.text.strip()
    except Exception as e:
        print(f"Error generating roast with Gemini: {str(e)}")
        return generate_local_roast(prompt)

# Main roast generation function that tries Gemini first, falls back to local
async def generate_roast_caption(prompt):
    if GEMINI_AVAILABLE:
        return await generate_gemini_roast(prompt)
    else:
        return generate_local_roast(prompt)

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
    
    if content.startswith('/hi'):
      await message.channel.send('''Hello there! What do you want to know about Mr. Nerve?
/truth - Get a random truth
/dare - Get a random dare
/addtruth - Add a truth
/adddare - Add a dare''')
      
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
        
intents = Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
