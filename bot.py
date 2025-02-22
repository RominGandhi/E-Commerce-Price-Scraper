import discord
from discord.ext import commands, tasks
import json
import asyncio
import re
from tracker import fetch_price_dynamic  
from supabase import create_client, Client 
import config  # Import configuration file

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

selectors = {}
try:
    with open("selectors/selectors.json", "r") as file:
        selectors = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    print("❌ ERROR: Invalid or missing selectors.json! Ensure it exists and is properly formatted.")


config_data = {}
try:
    with open("config.json", "r") as file:
        config_data = json.load(file)
    channel_id = int(config_data["channel_id"])  # Ensure channel_id is an integer
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"❌ ERROR: Invalid or missing config.json! ({e})")
    exit(1)

# ✅ Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Track active commands to prevent duplicate execution
active_commands = set()
bot_started = False  # Prevent multiple instances

### 📌 EVENT: BOT READY ###
@bot.event
async def on_ready():
    global bot_started
    if bot_started:
        return  # Prevent multiple executions
    bot_started = True  # Set flag to True

    print(f"✅ Bot logged in as {bot.user}")
    print(f"Bot is in these servers: {[guild.name for guild in bot.guilds]}")  # Debugging
    try:
        channel = await bot.fetch_channel(channel_id)
        await channel.send("🚀 Bot is now online and ready!")
    except Exception as e:
        print(f"⚠️ Could not send startup message: {e}")

    if not price_checker.is_running():
        price_checker.start()

### 📌 COMMAND: ADD PRODUCT ###
@bot.command()
async def add_product(ctx):
    """Guide the user to add a product step-by-step, storing the user ID."""

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    if ctx.author.id in active_commands:
        await ctx.send("⚠️ **You already have an active add_product command!**")
        return
    active_commands.add(ctx.author.id)

    try:
        answers = {}

        # ✅ Step 1: Store Name
        await ctx.send("🛒 **Enter the store name** (e.g., walmart.ca, amazon.ca, bestbuy.ca):")
        msg = await bot.wait_for("message", check=check, timeout=120)
        store = msg.content.strip().lower()

        if store not in selectors:
            await ctx.send(f"⚠️ **No selector found for {store}.** Ensure it's in `selectors.json`.")
            return
        answers["store"] = store

        # ✅ Step 2: Product Name
        await ctx.send("📦 **Enter the product name:**")
        msg = await bot.wait_for("message", check=check, timeout=120)
        answers["product_name"] = msg.content.strip()

        # ✅ Step 3: Product URL (Validate)
        while True:
            await ctx.send("🔗 **Enter the product URL:**")
            msg = await bot.wait_for("message", check=check, timeout=120)
            url = msg.content.strip()

            if not re.match(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", url):
                await ctx.send("⚠️ **Invalid URL! Please enter a valid product link.**")
                continue  # Ask again if invalid

            answers["url"] = url
            break  # Break loop if valid

        # ✅ Step 4: Target Price (Validate)
        while True:
            await ctx.send("💲 **Enter your target price:**")
            msg = await bot.wait_for("message", check=check, timeout=10)
            try:
                target_price = float(msg.content.strip())
                answers["target_price"] = target_price
                break  # Break loop if valid
            except ValueError:
                await ctx.send("⚠️ **Invalid price! Please enter a valid number.**")

        # ✅ Fetch Current Price (Handle Amazon Separately)
        if store == "amazon.ca":
            selector = {
                "whole": selectors[store].get("price_whole"),
                "fraction": selectors[store].get("price_fraction"),
            }
        else:
            selector = selectors[store].get("price")

        if not selector:
            await ctx.send(f"⚠️ **No price selector found for {store}.** Ensure it's in `selectors.json`.")
            return

        # ✅ Remove `await` since `fetch_price_dynamic()` is not async
        current_price = fetch_price_dynamic(url, store)

        if not current_price:
            await ctx.send("⚠️ **Could not fetch the current price.** Please check the URL.")
            return
        
        # ✅ Check if the current price is at or below the target price
        if current_price <= answers["target_price"]:
            await ctx.send(
                f"🎯 **{ctx.author.mention} Your target price matched **\n"
                f"💲 **Current Price:** ${current_price:.2f}\n"
                f"🎯 **Target Price:** ${answers['target_price']:.2f}\n"
                f"🔗 [Product Link]({url})"
            )


        # ✅ Save to Supabase
        supabase.table("products").insert({
            "user_id": ctx.author.id,
            "store": store,
            "product_name": answers["product_name"],
            "url": answers["url"],
            "css_selector": selector,  # Storing correct selector
            "target_price": answers["target_price"]
        }).execute()

        # ✅ Confirmation Message with Current Price
        await ctx.send(
            f"✅ **{ctx.author.mention} {answers['product_name']} added!**\n"
            f"💲 **Current Price:** ${current_price:.2f}\n"
            f"🎯 **Target Price:** ${answers['target_price']:.2f}\n"
            f"🔗 [Product Link]({url})"
        )

        # ✅ Notify immediately if the price is at or below target
        if current_price <= answers["target_price"]:
            await ctx.send(
                f"🎯 **{ctx.author.mention} Your target price matched or is lower!**\n"
                f"💲 **Current Price:** ${current_price:.2f}\n"
                f"🎯 **Target Price:** ${answers['target_price']:.2f}\n"
                f"🔗 [Product Link]({url})"
            )

    except asyncio.TimeoutError:
        await ctx.send("⏳ **You took too long to respond.** Try again!")

    finally:
        active_commands.discard(ctx.author.id)


### 📌 COMMAND: CHECK PRICE ###
@bot.command()
async def check_price(ctx, product_name: str):
    """Allow users to manually check the current price of their saved product."""
    response = supabase.table("products").select("url, css_selector").eq("user_id", ctx.author.id).eq("product_name", product_name).execute()
    product = response.data[0] if response.data else None


    if not product:
        await ctx.send(f"⚠️ **No product found with the name '{product_name}' for you.**")
        return

    url, selector = product
    price = await fetch_price_dynamic(url, selector)

    if price:
        await ctx.send(f"✅ **{ctx.author.mention} The current price of '{product_name}' is:** 💲${price:.2f}\n🔗 [Product Link]({url})")
    else:
        await ctx.send(f"⚠️ **Could not fetch the price for '{product_name}'.** Please check the URL or try again later.")

### 📌 AUTOMATED PRICE CHECK ###
@tasks.loop(minutes=5)
async def price_checker():
    """Automatically check product prices and notify if below or at the target price."""
    channel = await bot.fetch_channel(channel_id)

    response = supabase.table("products").select("*").execute()
    products = response.data  # Extract data from response

    for product in products:
        product_id = product["id"]
        user_id = product["user_id"]
        store = product["store"]
        product_name = product["product_name"]
        url = product["url"]
        css_selector = product["css_selector"]
        target_price = product["target_price"]

        price = fetch_price_dynamic(url, store)  

        if price:
            mention = f"<@{user_id}>"
            if price < target_price:
                await channel.send(f"🔥 **{mention} Price Drop Alert!** {product_name} is now ${price:.2f}!\n🔗 {url}")
            elif price == target_price:
                await channel.send(f"🎯 **{mention} Your target price matched!** {product_name} is now ${price:.2f}!\n🔗 {url}")


### 📌 COMMAND: SET TARGET PRICE ###
@bot.command()
async def set_target(ctx, product_name: str, target_price: float):
    """Allow users to update their target price for a specific product."""
    response = supabase.table("products").select("*").eq("user_id", ctx.author.id).eq("product_name", product_name).execute()
    product = response.data[0] if response.data else None

    if not product:
        await ctx.send(f"⚠️ **No product found with the name '{product_name}' for you.**")
        return

    supabase.table("products").update({"target_price": target_price}).eq("user_id", ctx.author.id).eq("product_name", product_name).execute()

    await ctx.send(f"✅ **{ctx.author.mention} Your target price for '{product_name}' has been updated to ${target_price:.2f}!**")


### 📌 COMMAND: REMOVE PRODUCT ###
@bot.command(name="remove_product")
async def remove_product(ctx, *, product_name: str):
    """Allow users to stop tracking a product using flexible name matching."""
    
    response = supabase.table("products").select("product_name").eq("user_id", ctx.author.id).execute()
    products = [p["product_name"].strip().lower() for p in response.data]

    if not products:
        await ctx.send(f"⚠️ **You are not tracking any products.**")
        return

    search_name = product_name.strip().lower()
    matched_product = next((p for p in products if search_name in p), None)

    if not matched_product:
        await ctx.send(f"⚠️ **No product found with the name '{product_name}' for you.**")
        return

    supabase.table("products").delete().eq("user_id", ctx.author.id).eq("product_name", matched_product).execute()

    await ctx.send(f"🗑️ **{ctx.author.mention} You have successfully stopped tracking '{matched_product}'.**")



### 📌 COMMAND: VIEW ACTIVE ALERTS ###
@bot.command(name="alerts")
async def alerts(ctx):
    response = supabase.table("products").select("product_name, target_price").eq("user_id", ctx.author.id).execute()
    products = response.data

    if not products:
        await ctx.send(f"⚠️ **You have no active price alerts.** Use `!add_product` to start tracking.")
        return

    alert_list = "\n".join([f"🔹 **{p['product_name']}** → 🎯 Target Price: **${p['target_price']:.2f}**" for p in products])

    embed = discord.Embed(
        title="📢 Your Active Price Alerts",
        description=alert_list,
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)



### 📌 COMMAND: LIST TRACKED PRODUCTS ###
@bot.command()
async def list_products(ctx):
    response = supabase.table("products").select("product_name, url").eq("user_id", ctx.author.id).execute()
    products = response.data

    if not products:
        await ctx.send(f"⚠️ **You are not tracking any products.** Use `!add_product` to start tracking.")
        return

    product_list = "\n".join([f"🔹 **[{p['product_name']}]({p['url']})**" for p in products])

    embed = discord.Embed(
        title="🛍️ Your Tracked Products",
        description=product_list,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


# ✅ Remove built-in help command to avoid conflicts
bot.remove_command("help")

@bot.command(name="help")
async def help_menu(ctx):
    """Engaging help command with categories and emojis."""
    
    embed = discord.Embed(
        title="📌 Price Tracking Bot - Help Menu",
        description="Welcome to the **Price Tracking Bot**! 🛍️ Get notified when product prices drop!\n\n"
                    "🔹 **Use the commands below to track products, check prices, and manage your alerts.**",
        color=discord.Color.blue()
    )

    # ✅ Product Tracking Commands
    embed.add_field(
        name="🛒 **Product Tracking**",
        value=(
            "**`!add_product`** → Add a new product for tracking.\n"
            "**`!check_price <product>`** → Check the current price of a saved product.\n"
            "**`!list_products`** → View all products you are tracking."
        ),
        inline=False
    )

    # ✅ Price Alert Commands
    embed.add_field(
        name="📉 **Price Alerts**",
        value=(
            "**`!set_target <product> <price>`** → Set a target price for a product.\n"
            "**`!remove_product <product>`** → Stop tracking a product.\n"
            "**`!alerts`** → View all your active price alerts."
        ),
        inline=False
    )

    # ✅ Bot Management
    embed.add_field(
        name="⚙️ **Bot Management**",
        value=(
            "**`!help`** → Show this help menu.\n"
            "**`!shutdown`** → (Admin only) Shut down the bot."
        ),
        inline=False
    )

    embed.set_footer(text="🚀 Stay notified and save money on your favorite products!")
    
    await ctx.send(embed=embed)



# ✅ Run bot
bot.run(config.BOT_TOKEN)
