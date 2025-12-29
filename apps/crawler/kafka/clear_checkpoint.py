#!/usr/bin/env python3
"""
Clear Kafka Producer Checkpoint
Xóa file processed_urls.txt để resend tất cả records
"""
import os
import sys

def clear_checkpoint():
    """Clear checkpoint file"""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    checkpoint_file = os.path.join(base_dir, "crawler", "kafka", "processed_urls.txt")
    
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print(f"✅ Cleared checkpoint file: {checkpoint_file}")
        print("   Producer will resend all records on next run.")
    else:
        print(f"ℹ️  Checkpoint file not found: {checkpoint_file}")
        print("   No checkpoint to clear.")

if __name__ == "__main__":
    clear_checkpoint()

