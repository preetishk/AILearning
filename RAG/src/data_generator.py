"""
Warranty document data for demo SKUs.
Designed to highlight cases where BM25 (exact match) outperforms pure semantic RAG.
"""

WARRANTY_DOCS = [
    {
        "id": "doc_LPT-2024-PRO",
        "sku": "LPT-2024-PRO",
        "title": "Laptop Pro Series Warranty",
        "content": (
            "SKU: LPT-2024-PRO\n"
            "Product: Laptop Pro 15 (2024 Edition)\n"
            "Warranty Period: 2 years from date of purchase\n\n"
            "Coverage:\n"
            "- Manufacturing defects in materials and workmanship\n"
            "- Battery replacement if capacity drops below 80% within 1 year\n"
            "- Free on-site repair service within 30 days of purchase\n\n"
            "Exclusions:\n"
            "- Physical damage, liquid spills, or accidental drops\n"
            "- Damage caused by unauthorized modifications\n"
            "- Normal wear and tear on keyboard keys and screen coating\n\n"
            "Claim Process:\n"
            "Contact support at 1-800-SKU-HELP with SKU LPT-2024-PRO and proof of purchase.\n"
            "Depot repair turnaround: 5-7 business days."
        ),
    },
    {
        "id": "doc_PHN-X500-BLK",
        "sku": "PHN-X500-BLK",
        "title": "Smartphone X500 Black Warranty",
        "content": (
            "SKU: PHN-X500-BLK\n"
            "Product: Smartphone X500 (Black Variant)\n"
            "Warranty Period: 1 year from date of purchase\n\n"
            "Coverage:\n"
            "- Defects in hardware components and factory settings\n"
            "- Screen dead pixels (more than 3 pixels)\n"
            "- Charging port malfunction not caused by user damage\n\n"
            "Exclusions:\n"
            "- Screen cracks or breaks from drops\n"
            "- Water damage beyond IP67 rating limits\n"
            "- Software issues caused by third-party apps\n\n"
            "Claim Process:\n"
            "Register PHN-X500-BLK at warranty.example.com within 30 days.\n"
            "Replacement units shipped within 3 business days for approved claims."
        ),
    },
    {
        "id": "doc_TAB-8HD-SLVR",
        "sku": "TAB-8HD-SLVR",
        "title": "Tablet 8 HD Silver Warranty",
        "content": (
            "SKU: TAB-8HD-SLVR\n"
            "Product: Tablet 8 HD (Silver Edition)\n"
            "Warranty Period: 18 months from date of purchase\n\n"
            "Coverage:\n"
            "- Display defects including backlight bleeding\n"
            "- Touch screen unresponsiveness under normal use\n"
            "- Speaker and microphone hardware failures\n\n"
            "Exclusions:\n"
            "- Damage from third-party accessories or chargers\n"
            "- Rooted or modified operating systems void warranty\n"
            "- Cosmetic scratches or dents from regular use\n\n"
            "Claim Process:\n"
            "Ship TAB-8HD-SLVR unit to nearest service center with receipt.\n"
            "Express replacement available for premium support tier customers."
        ),
    },
    {
        "id": "doc_HDR-NC700-WHT",
        "sku": "HDR-NC700-WHT",
        "title": "Headphones Noise Cancelling 700 White Warranty",
        "content": (
            "SKU: HDR-NC700-WHT\n"
            "Product: Noise Cancelling Headphones 700 (White)\n"
            "Warranty Period: 1 year from date of purchase\n\n"
            "Coverage:\n"
            "- Noise cancellation hardware failures\n"
            "- Bluetooth connectivity issues not caused by user\n"
            "- Cushion and headband structural defects within 6 months\n\n"
            "Exclusions:\n"
            "- Cable damage from improper storage\n"
            "- Damage from extreme temperatures or humidity\n"
            "- Channel imbalance caused by third-party EQ applications\n\n"
            "Claim Process:\n"
            "Contact service center with HDR-NC700-WHT serial number.\n"
            "Mail-in repair only; no on-site service for audio products."
        ),
    },
    {
        "id": "doc_MNT-27QHD-BLK",
        "sku": "MNT-27QHD-BLK",
        "title": "Monitor 27 QHD Black Warranty",
        "content": (
            "SKU: MNT-27QHD-BLK\n"
            "Product: 27-inch QHD Monitor (Black)\n"
            "Warranty Period: 3 years from date of purchase\n\n"
            "Coverage:\n"
            "- Dead pixels (more than 5 pixels in non-edge zones)\n"
            "- Backlight failure or severe uniformity issues\n"
            "- Port failures: HDMI, DisplayPort, USB-C\n\n"
            "Exclusions:\n"
            "- Burn-in from prolonged static image display\n"
            "- Physical screen damage or cracks\n"
            "- Power surge damage (use of surge protector recommended)\n\n"
            "Claim Process:\n"
            "Log defect at support portal using SKU MNT-27QHD-BLK.\n"
            "On-site panel replacement available within metro areas.\n"
            "Panel swap guaranteed within 10 business days."
        ),
    },
    {
        "id": "doc_KBD-MECH-RGB",
        "sku": "KBD-MECH-RGB",
        "title": "Mechanical Keyboard RGB Warranty",
        "content": (
            "SKU: KBD-MECH-RGB\n"
            "Product: Mechanical Keyboard with RGB Backlighting\n"
            "Warranty Period: 2 years from date of purchase\n\n"
            "Coverage:\n"
            "- Switch mechanism failures (actuation force deviation >20%)\n"
            "- USB cable connector failures\n"
            "- RGB LED complete failure (not individual keys)\n\n"
            "Exclusions:\n"
            "- Keycap wear or fading from normal use\n"
            "- Liquid spills void warranty immediately\n"
            "- Firmware bricking from unauthorized user modification\n\n"
            "Claim Process:\n"
            "Submit claim at kbd-support.example.com with KBD-MECH-RGB purchase proof.\n"
            "Depot repair: 7-10 business days.\n"
            "Advance replacement available for business accounts only."
        ),
    },
]
