#!/usr/bin/env python3
"""
Test script to verify model configuration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.config.settings import settings

def test_model_configs():
    print("Testing model configurations...")
    
    for model_type, config in settings.MODEL_CONFIGS.items():
        print(f"\n{model_type}:")
        print(f"  Model: {config['model']}")
        print(f"  Description: {config['description']}")
        print(f"  Use case: {config['use_case']}")

if __name__ == "__main__":
    test_model_configs()
