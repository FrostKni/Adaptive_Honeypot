#!/usr/bin/env python3
"""
Test script to verify AI provider connections
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_openai():
    """Test OpenAI connection"""
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ OpenAI: API key not found in .env")
            return False
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI: Connection successful")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI: Connection failed - {e}")
        return False

def test_anthropic():
    """Test Anthropic connection"""
    try:
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("❌ Anthropic: API key not found in .env")
            return False
        
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test'"}]
        )
        
        print("✅ Anthropic: Connection successful")
        print(f"   Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic: Connection failed - {e}")
        return False

def test_gemini():
    """Test Google Gemini connection"""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            print("❌ Gemini: API key not found in .env")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'test'")
        
        print("✅ Gemini: Connection successful")
        print(f"   Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini: Connection failed - {e}")
        return False

def main():
    print("🧪 Testing AI Provider Connections")
    print("=" * 50)
    print()
    
    # Check which provider is configured
    provider = os.getenv("AI_PROVIDER", "").lower()
    model = os.getenv("AI_MODEL", "")
    
    print(f"Configured Provider: {provider or 'Not set'}")
    print(f"Configured Model: {model or 'Not set'}")
    print()
    print("-" * 50)
    print()
    
    results = {}
    
    # Test all providers
    print("Testing OpenAI...")
    results['openai'] = test_openai()
    print()
    
    print("Testing Anthropic...")
    results['anthropic'] = test_anthropic()
    print()
    
    print("Testing Gemini...")
    results['gemini'] = test_gemini()
    print()
    
    print("-" * 50)
    print()
    print("📊 Summary:")
    print(f"   OpenAI: {'✅ Working' if results['openai'] else '❌ Not configured or failed'}")
    print(f"   Anthropic: {'✅ Working' if results['anthropic'] else '❌ Not configured or failed'}")
    print(f"   Gemini: {'✅ Working' if results['gemini'] else '❌ Not configured or failed'}")
    print()
    
    # Check if configured provider works
    if provider and provider in results:
        if results[provider]:
            print(f"✅ Your configured provider ({provider}) is working!")
        else:
            print(f"⚠️  Your configured provider ({provider}) is not working!")
            print(f"   Please check your {provider.upper()}_API_KEY in .env")
    else:
        print("⚠️  No AI provider configured in .env")
        print("   Please set AI_PROVIDER in your .env file")
    
    print()
    print("💡 Tip: See AI_PROVIDER_GUIDE.md for detailed configuration")
    print()

if __name__ == "__main__":
    main()
