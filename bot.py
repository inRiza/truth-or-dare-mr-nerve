from discord import Client, Intents, Embed, Color
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

# Create a styled embed for messages
def create_embed(title, description, color=Color.blue()):
    embed = Embed(title=title, description=description, color=color)
    embed.set_footer(text="Mr. Nerve Bot")
    return embed

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
      embed = create_embed(
        "👋 Hello there!", 
        "I am Mr. Nerve, your friendly Discord bot!\n\n**Available Commands:**\n" +
        "`/truth` - Get a random truth\n" +
        "`/dare` - Get a random dare\n" +
        "`/addtruth` - Add a truth\n" +
        "`/adddare` - Add a dare\n" +
        "`/roastmode` - Activate roast mode",
        Color.green()
      )
      await message.channel.send(embed=embed)
    
    elif content.startswith('/admin'):
      input_password = content[len('/admin '):].strip()
      if input_password != os.getenv("ADMIN_PASSWORD"):
        embed = create_embed("❌ Access Denied", "Incorrect password!", Color.red())
        await message.channel.send(embed=embed)
        return
        
      self.admin_active = True
      embed = create_embed(
        "✅ Admin Mode Activated", 
        "Hello Admin! What do you want to do?\n\n" +
        "`/deleteall` - Delete all truths and dares\n" +
        "`/deletealltruth` - Delete all truths\n" +
        "`/deletealldare` - Delete all dares\n" +
        "`/showtruths` - Show all truths\n" +
        "`/showdares` - Show all dares",
        Color.gold()
      )
      await message.channel.send(embed=embed)
      
    elif self.admin_active:
      if content.startswith('/deleteall'):
        delete_all_truths()
        delete_all_dares()
        embed = create_embed("✅ Success", "All truths and dares have been deleted!", Color.green())
        await message.channel.send(embed=embed)
        
      elif content.startswith('/deletealltruth'):
        delete_all_truths()
        embed = create_embed("✅ Success", "All truths have been deleted!", Color.green())
        await message.channel.send(embed=embed)
      
      elif content.startswith('/deletealldare'):
        delete_all_dares()
        embed = create_embed("✅ Success", "All dares have been deleted!", Color.green())
        await message.channel.send(embed=embed)
      
      elif content.startswith('/showtruths'):
        conn = sqlite3.connect('truthordare.db')
        c = conn.cursor()
        c.execute("SELECT content FROM truths")
        truths = c.fetchall()
        conn.close()
        
        if truths:
          embed = create_embed("📝 All Truths", "Here are all the truths in the database:", Color.blue())
          await message.channel.send(embed=embed)
          
          # Send truths in chunks to avoid message length limits
          truth_text = ""
          for i, truth in enumerate(truths, 1):
            truth_text += f"**{i}.** {truth[0]}\n"
            if i % 10 == 0 or i == len(truths):
              chunk_embed = create_embed("", truth_text, Color.blue())
              await message.channel.send(embed=chunk_embed)
              truth_text = ""
        else:
          embed = create_embed("📝 All Truths", "No truths found in the database.", Color.blue())
          await message.channel.send(embed=embed)
        
      elif content.startswith('/showdares'):
        conn = sqlite3.connect('truthordare.db')
        c = conn.cursor()
        c.execute("SELECT content FROM dares")
        dares = c.fetchall()
        conn.close()
        
        if dares:
          embed = create_embed("🎯 All Dares", "Here are all the dares in the database:", Color.purple())
          await message.channel.send(embed=embed)
          
          # Send dares in chunks to avoid message length limits
          dare_text = ""
          for i, dare in enumerate(dares, 1):
            dare_text += f"**{i}.** {dare[0]}\n"
            if i % 10 == 0 or i == len(dares):
              chunk_embed = create_embed("", dare_text, Color.purple())
              await message.channel.send(embed=chunk_embed)
              dare_text = ""
        else:
          embed = create_embed("🎯 All Dares", "No dares found in the database.", Color.purple())
          await message.channel.send(embed=embed)
      
    elif content.startswith('/roastmode'):
      self.roast_active = True
      embed = create_embed("🔥 Roast Mode Activated", "Prepare to be roasted!", Color.orange())
      await message.channel.send(embed=embed)
    
    elif content.startswith('/truth'):
      truth = get_random_entry('truths')
      if truth:
        embed = create_embed("📝 Truth", f"**{truth}**", Color.blue())
        await message.channel.send(embed=embed)
        
        if self.roast_active:
          roast_prompt = await generate_roast_caption(truth)
          roast_embed = create_embed("🔥 Roast", f"**{roast_prompt}**", Color.red())
          await message.channel.send(embed=roast_embed)
      else:
        embed = create_embed("❌ Error", "No truths found in the database. Add some with `/addtruth`!", Color.red())
        await message.channel.send(embed=embed)
    
    elif content.startswith('/dare'):
      dare = get_random_entry('dares')
      if dare:
        embed = create_embed("🎯 Dare", f"**{dare}**", Color.purple())
        await message.channel.send(embed=embed)
      else:
        embed = create_embed("❌ Error", "No dares found in the database. Add some with `/adddare`!", Color.red())
        await message.channel.send(embed=embed)
      
    elif content.startswith('/addtruth'):
      add_truth = content[len('/addtruth '):].strip()
      if add_truth:
        add_entry('truths', add_truth)
        embed = create_embed("✅ Success", f"Truth added: **{add_truth}**", Color.green())
        await message.channel.send(embed=embed)
      else:
        embed = create_embed("❌ Error", "Please provide a truth to add.", Color.red())
        await message.channel.send(embed=embed)
      
    elif content.startswith('/adddare'):
      add_dare = content[len('/adddare '):].strip()
      if add_dare:
        add_entry('dares', add_dare)
        embed = create_embed("✅ Success", f"Dare added: **{add_dare}**", Color.green())
        await message.channel.send(embed=embed)
      else:
        embed = create_embed("❌ Error", "Please provide a dare to add.", Color.red())
        await message.channel.send(embed=embed)

# Create and run the client
client = MyClient(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
