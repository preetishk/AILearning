# Protobuf vs JSON — PoC

A hands-on comparison of [Protocol Buffers (protobuf)](https://protobuf.dev/) and JSON for serializing structured data, demonstrating protobuf's size and encoding efficiency.

---

## Folder Structure

```
protobuf/
├── protodef/
│   ├── order.proto         # Message schema definition
│   └── order_pb2.py        # Auto-generated Python bindings (from protoc)
├── src/
│   └── protobuf_example.py # Serialise an order in both JSON and protobuf,
│                           #   write timestamped comparison report
└── output/                 # Timestamped report files (git-ignored)
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | |
| `protobuf` library | `pip install protobuf` |
| `protoc` compiler | Only needed to regenerate `order_pb2.py` |

---

## Setup

```bash
pip install protobuf
```

> `protodef/order_pb2.py` is already included so you don't need `protoc` just to run the example.

---

## Running the Example

```bash
python src/protobuf_example.py
```

This will:
1. Serialise a sample `Order` message as **JSON** and **Protobuf binary**
2. Compare the sizes
3. Write a timestamped report to `output/`

### Sample output
```
JSON Size          : 341 bytes
Protobuf Size      : 161 bytes
Size Reduction     : 180 bytes
Percentage Smaller : 52.8%
```

---

## Schema

The `Order` message defined in [protodef/order.proto](protodef/order.proto):

```proto
message Order {
  string order_id     = 1;
  Customer customer   = 2;
  repeated OrderItem items = 3;
  double total_amount = 4;
  string status       = 5;
  string created_at   = 6;
}

message Customer {
  int32  customer_id = 1;
  string name        = 2;
  string email       = 3;
}

message OrderItem {
  int32  product_id = 1;
  string name       = 2;
  int32  quantity   = 3;
  double price      = 4;
}
```

---

## Regenerating Protobuf Bindings

If you modify `order.proto`, regenerate the Python bindings with:

```bash
protoc --python_out=protodef protodef/order.proto
```

---

## Key Takeaway

Protobuf encodes data as a compact binary format — typically **40–60% smaller** than equivalent JSON — making it ideal for high-throughput APIs and network transmission where payload size matters.
