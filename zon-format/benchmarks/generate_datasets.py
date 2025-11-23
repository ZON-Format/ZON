import json
import random
import datetime
import os
from faker import Faker

fake = Faker()
DATA_DIR = "benchmarks/data"
Faker.seed(12345)
random.seed(12345)

DEPARTMENTS = ['Engineering', 'Sales', 'Marketing', 'HR', 'Operations', 'Finance']
PRODUCT_NAMES = ['Wireless Mouse', 'USB Cable', 'Laptop Stand', 'Keyboard', 'Webcam', 'Headphones', 'Monitor', 'Desk Lamp']
ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

def generate_employees(count=100):
    employees = []
    for i in range(count):
        emp = {
            "id": i + 1,
            "name": fake.name(),
            "email": fake.email().lower(),
            "department": DEPARTMENTS[i % len(DEPARTMENTS)],
            "salary": random.randint(45000, 150000),
            "yearsExperience": random.randint(1, 25),
            "active": random.random() < 0.8
        }
        employees.append(emp)
    return {"employees": employees}

def generate_analytics(days=60, start_date='2025-01-01'):
    metrics = []
    date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(days):
        current_date = date + datetime.timedelta(days=i)
        
        base_views = 5000
        is_weekend = current_date.weekday() >= 5
        weekend_multiplier = 0.7 if is_weekend else 1.0
        
        views = int(base_views * weekend_multiplier + random.randint(-1000, 3000))
        clicks = int(views * random.uniform(0.02, 0.08))
        conversions = int(clicks * random.uniform(0.05, 0.15))
        avg_order_value = random.uniform(49.99, 299.99)
        revenue = round(conversions * avg_order_value, 2)
        bounce_rate = round(random.uniform(0.3, 0.7), 2)
        
        metrics.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "views": views,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "bounceRate": bounce_rate
        })
    return {"metrics": metrics}

def generate_orders(count=50):
    orders = []
    for i in range(count):
        customer_id = (i % 20) + 1
        item_count = random.randint(1, 4)
        
        items = []
        for j in range(item_count):
            price = round(random.uniform(9.99, 199.99), 2)
            quantity = random.randint(1, 5)
            items.append({
                "sku": f"SKU-{fake.lexify(text='??????').upper()}",
                "name": PRODUCT_NAMES[j % len(PRODUCT_NAMES)],
                "quantity": quantity,
                "price": price
            })
            
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        subtotal = round(subtotal, 2)
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + tax, 2)
        
        order = {
            "orderId": f"ORD-{str(i + 1).zfill(4)}",
            "customer": {
                "id": customer_id,
                "name": fake.name(),
                "email": fake.email().lower(),
                "phone": fake.phone_number()
            },
            "items": items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "status": ORDER_STATUSES[i % len(ORDER_STATUSES)],
            "orderDate": fake.date_this_year().strftime("%Y-%m-%d") # Simplified date
        }
        orders.append(order)
    return {"orders": orders}

def generate_complex_nested(rows=1000):
    data = []
    for i in range(rows):
        # Deep nesting and irregular structures
        row = {
            "id": f"evt_{i}",
            "meta": {
                "timestamp": 1670000000 + i,
                "source": random.choice(["web", "mobile", "api"]),
                "context": {
                    "ip": fake.ipv4(),
                    "user_agent": fake.user_agent() if i % 2 == 0 else None # Sparse
                }
            },
            "payload": {
                "user": {
                    "id": i + 1000,
                    "profile": {
                        "username": fake.user_name(),
                        "preferences": {
                            "theme": "dark",
                            "notifications": {
                                "email": True,
                                "push": False,
                                "sms": i % 5 == 0 # Occasional
                            }
                        }
                    }
                },
                "data": {
                    "action": "click",
                    "target": f"btn_{random.randint(1, 10)}",
                    "coordinates": {"x": random.randint(0, 1920), "y": random.randint(0, 1080)}
                }
            }
        }
        data.append(row)
    
    with open(os.path.join(DATA_DIR, "complex_nested.json"), "w") as f:
        json.dump(data, f, indent=2)
    print("Generated complex_nested.json")

if __name__ == "__main__":
    print("Generating datasets...")
    
    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(os.path.join(DATA_DIR, "employees.json"), "w") as f:
        json.dump(generate_employees(100), f, indent=2)
    print("Generated employees.json")
    
    with open(os.path.join(DATA_DIR, "analytics.json"), "w") as f:
        json.dump(generate_analytics(60), f, indent=2)
    print("Generated analytics.json")
    
    with open("benchmarks/data/orders.json", "w") as f:
        json.dump(generate_orders(50), f, indent=2)
    print("Generated orders.json")
    
    generate_complex_nested()
    
    print("Done.")
