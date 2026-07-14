import sys
import os
import json
from datetime import datetime

# ====================== ROBUST PATH FIX ======================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))

sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'protodef'))

try:
    from protodef import order_pb2
    print("✅ Successfully imported order_pb2")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
# ============================================================

def main():
    # ==================== 1. Sample JSON Payload ====================
    json_payload = {
        "order_id": "ORD-987654",
        "customer": {
            "customer_id": 45678,
            "name": "Rahul Sharma",
            "email": "rahul.sharma@example.com"
        },
        "items": [
            {
                "product_id": 101,
                "name": "Wireless Headphones",
                "quantity": 2,
                "price": 49.99
            },
            {
                "product_id": 202,
                "name": "USB Cable",
                "quantity": 3,
                "price": 9.99
            }
        ],
        "total_amount": 119.95,
        "status": "SHIPPED",
        "created_at": "2026-05-20T14:30:00Z"
    }

    json_string = json.dumps(json_payload, separators=(',', ':'))
    json_size = len(json_string.encode('utf-8'))

    # ==================== 2. Create Protobuf Output ====================
    order = order_pb2.Order()
    
    order.order_id = "ORD-987654"
    order.total_amount = 119.95
    order.status = "SHIPPED"
    order.created_at = "2026-05-20T14:30:00Z"

    order.customer.customer_id = 45678
    order.customer.name = "Rahul Sharma"
    order.customer.email = "rahul.sharma@example.com"

    item1 = order.items.add()
    item1.product_id = 101
    item1.name = "Wireless Headphones"
    item1.quantity = 2
    item1.price = 49.99

    item2 = order.items.add()
    item2.product_id = 202
    item2.name = "USB Cable"
    item2.quantity = 3
    item2.price = 9.99

    protobuf_binary = order.SerializeToString()
    protobuf_size = len(protobuf_binary)

    # ==================== Write JSON and Protobuf to Timestamped File ====================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"data_output_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== JSON PAYLOAD ===\n")
        f.write(json_string)
        f.write(f"\n\nJSON Size: {json_size} bytes\n")
        f.write("="*50 + "\n\n")
        
        f.write("=== PROTOBUF BINARY (as hex) ===\n")
        f.write(protobuf_binary.hex())
        f.write(f"\n\nProtobuf Size: {protobuf_size} bytes\n")
        f.write("="*50)

    # Console Output
    print(f"\n✅ Output successfully written to:")
    print(f"   {output_path}")
    print(f"\nJSON Size      : {json_size} bytes")
    print(f"Protobuf Size  : {protobuf_size} bytes")

if __name__ == "__main__":
    main()