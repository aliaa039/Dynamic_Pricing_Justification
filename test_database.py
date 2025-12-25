from .src.external.price_database import PriceDatabase

db = PriceDatabase()

# Test 1: Check if OPPO Reno 12 exists
print("\nTest 1: OPPO Reno 12 5G")
result = db.get_price("OPPO", "Reno 12 5G")
if result:
    print(f"✅ Found: ${result['price']} from {result['source']}")
else:
    print("❌ Not found in database")

# Test 2: List all products
print("\nTest 2: All Products")
all_products = db.list_all()
print(f"Total products: {len(all_products)}")
for key, product in all_products.items():
    print(f"  - {product['brand']} {product['model']}: ${product['price']}")

# Test 3: Database stats
print("\nTest 3: Statistics")
stats = db.get_stats()
print(f"Total: {stats['total_products']}")
print(f"Categories: {stats['categories']}")
print(f"Brands: {stats['brands']}")