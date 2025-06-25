import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', 0))
SECRET_GROUP_LINK = os.getenv('SECRET_GROUP_LINK')
