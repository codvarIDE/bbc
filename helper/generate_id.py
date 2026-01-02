import random
import string
from datetime import datetime

def generate_patient_id(prefix="BC"):
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{date_part}-{random_part}"
