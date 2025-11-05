# history.py

import os
from telegram import Update
from telegram.ext import ContextTypes
import database as db

# --- Admin Check ---
# main.py က global list တွေကို ဒီ file က မမြင်နိုင်တဲ့အတွက်၊
# Admin list ကို ဒီ file အတွက် သီးသန့် load လုပ်ရပါမယ်။
try:
    ADMIN_ID = int(os.environ.get("ADMIN_ID"))
    ADMIN_IDS = db.load_admin_ids(ADMIN_ID)
except Exception as e:
    print(f"CRITICAL: history.py failed to load admin IDs: {e}")
    ADMIN_ID = 0
    ADMIN_IDS = []

def is_admin(user_id):
    """Check if user is any admin"""
    return int(user_id) in ADMIN_IDS

# --- History Command Handler ---

async def clear_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to clear a user's order and topup history.
    Usage: /clearhistory <user_id>
    """
    admin_user_id = str(update.effective_user.id)
    
    # 1. Admin Check
    if not is_admin(admin_user_id):
        await update.message.reply_text("❌ သင်သည် admin မဟုတ်ပါ။")
        return

    # 2. Argument Check
    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text(
            "❌ ***Format မှားနေပါတယ်!***\n\n"
            "***အသုံးပြုနည်း:*** `/clearhistory <user_id>`\n"
            "***ဥပမာ:*** `/clearhistory 123456789`",
            parse_mode="Markdown"
        )
        return
        
    target_user_id = args[0]

    # 3. Check if user exists
    user_doc = db.get_user(target_user_id)
    if not user_doc:
        await update.message.reply_text(f"❌ User ID `{target_user_id}` ကို Database တွင် မတွေ့ပါ။")
        return
        
    # 4. Execute deletion from DB
    try:
        success = db.clear_user_history(target_user_id)
        if success:
            await update.message.reply_text(
                f"✅ **မှတ်တမ်း ရှင်းလင်းပြီးပါပြီ!**\n\n"
                f"👤 ***User ID:*** `{target_user_id}`\n"
                f"📋 ***Status:*** Orders နှင့် Topups အားလုံး ဖျက်ပြီးပါပြီ။",
                parse_mode="Markdown"
            )
            
            # Notify the user (Optional)
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text="📋 ***Admin's Notice***\n\n"
                         "သင်၏ အော်ဒါ နှင့် ငွေဖြည့် မှတ်တမ်းများအားလုံးကို Admin မှ ရှင်းလင်းလိုက်ပါသည်။"
                )
            except Exception as e:
                print(f"Could not notify user {target_user_id} about history wipe: {e}")

        else:
            await update.message.reply_text(
                f"⚠️ **မအောင်မြင်ပါ!**\n\n"
                f"👤 ***User ID:*** `{target_user_id}`\n"
                f"📋 ***Status:*** User ကို တွေ့ရှိသော်လည်း မှတ်တမ်းများ မဖျက်နိုင်ပါ။ (DB Error)",
                parse_mode="Markdown"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error ဖြစ်သွားပါသည်: {str(e)}")
