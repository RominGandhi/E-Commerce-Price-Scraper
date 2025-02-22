# **📌 E-Commerce Price Scraper Bot**  
🚀 A **Discord bot** that tracks product prices from multiple e-commerce websites and notifies users when their target price is reached! Uses **Supabase**, **Selenium**, and **discord.py**.

---

## **📝 Features**  
👉 **Track product prices** from Amazon, Walmart, BestBuy, and more  
👉 **Receive alerts** when the price drops below your target  
👉 **Stores product details** using Supabase  
👉 **Easy commands** for adding/removing products  
👉 **Automated price checking every 5 minutes**  

---

## **📦 Installation & Setup**  

### **1️⃣ Clone the Repository**  
```bash
git clone https://github.com/RominGandhi/E-Commerce-Price-Scraper.git
cd E-Commerce-Price-Scraper
```

### **2️⃣ Install Dependencies**  
Ensure you have **Python 3.10+** installed, then run:  
```bash
pip install -r requirements.txt
```

### **3️⃣ Configure Environment Variables**  
All necessary files are already in the repository. Simply update `config.json` with your **Supabase credentials** and **Discord bot token**:

1. Open `config.json` and update the following fields:
```json
{
  "BOT_TOKEN": "your_discord_bot_token",
  "SUPABASE_URL": "your_supabase_url",
  "SUPABASE_KEY": "your_supabase_key",
  "channel_id": "your_discord_channel_id"
}
```

2. If you haven't already, create a **Supabase** project at [supabase.com](https://supabase.com) and retrieve your credentials.

---

## **📂 Database Schema (Supabase SQL)**  
To set up your database in **Supabase**, execute the following SQL script:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    store TEXT NOT NULL,
    product_name TEXT NOT NULL,
    url TEXT NOT NULL,
    css_selector JSONB NOT NULL,
    target_price DECIMAL(10, 2) NOT NULL
);
```

This table stores product tracking information for users, including their **Discord user ID**, store name, product details, and target price.

---

## **📌 Usage**  

### **Run the Bot**  
```bash
python bot.py
```

### **Discord Commands**  
| Command | Description |
|---------|-------------|
| `!add_product` | Add a product to track |
| `!check_price <product>` | Manually check the price |
| `!set_target <product> <price>` | Update target price |
| `!remove_product <product>` | Remove a product from tracking |
| `!alerts` | View active alerts |
| `!list_products` | Show tracked products |
| `!help` | Show help menu |

---

## **🛠️ Technologies Used**  
- **Python 3.10+**  
- **Discord.py** – for bot interactions  
- **Selenium** – for dynamic web scraping  
- **Supabase** – for database storage  
- **ChromeDriver** – for browser automation  

---

## **💡 Contributing**  
1. Fork the repository  
2. Create a new branch: `git checkout -b feature-name`  
3. Commit your changes: `git commit -m "Add feature"`  
4. Push to the branch: `git push origin feature-name`  
5. Submit a pull request  

---

## **📝 License**  
MIT License. See `LICENSE` for details.  

---
