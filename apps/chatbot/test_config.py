"""Test script to verify config loading."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import config

print("=" * 80)
print("Config Test - Verifying AWS Credentials Loading")
print("=" * 80)
print()
print(f"AWS_ACCESS_KEY_ID: {'*' * 10 if config.AWS_ACCESS_KEY_ID else '[EMPTY]'}")
print(
    f"AWS_SECRET_ACCESS_KEY: {'*' * 10 if config.AWS_SECRET_ACCESS_KEY else '[EMPTY]'}"
)
print(f"AWS_REGION: {config.AWS_REGION}")
print(f"BEDROCK_MODEL_REGION: {config.BEDROCK_MODEL_REGION}")
print(f"BEDROCK_EMBEDDING_MODEL: {config.BEDROCK_EMBEDDING_MODEL}")
print(f"BEDROCK_LLM_MODEL: {config.BEDROCK_LLM_MODEL}")
print()

if not config.AWS_ACCESS_KEY_ID or not config.AWS_SECRET_ACCESS_KEY:
    print("❌ ERROR: AWS credentials are EMPTY!")
    print()
    print("Please ensure your .env file contains:")
    print("  AWS_ACCESS_KEY_ID=your_key_here")
    print("  AWS_SECRET_ACCESS_KEY=your_secret_here")
    sys.exit(1)
else:
    print("✅ AWS credentials loaded successfully!")
    sys.exit(0)
