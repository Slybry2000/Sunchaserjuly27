#!/usr/bin/env python3
"""
Generate a stock photo acquisition list for Sunshine Spotter.
This helps identify exactly what images we need to source.
"""

import sys
import os

# Add Frontend to path to import the image service specs
sys.path.append(os.path.join(os.path.dirname(__file__), 'Frontend', 'lib'))

def generate_photo_requirements():
    """Generate requirements for stock photo acquisition"""
    
    categories = {
        'forest': 'Dense woodland with hiking trails - Pacific Northwest old growth forest',
        'gorge': 'River valley with dramatic cliffs - Columbia River Gorge style landscape', 
        'beach': 'Coastal area with ocean views - Oregon/Washington coast with dramatic rocks',
        'lake': 'Freshwater body with scenic shores - Mountain lake with forest backdrop',
        'mountain': 'High-elevation peak with vistas - Cascade Range snow-capped peak',
        'valley': 'Low-lying area with open landscapes - Agricultural valley with mountains',
        'urban park': 'City park with recreational facilities - Seattle/Portland urban green space',
        'park': 'Natural park area with trails - State/national park with hiking paths',
        'island': 'Island location with water views - San Juan Islands or similar',
        'climbing': 'Rock climbing area with challenging routes - Smith Rock style climbing area',
        'trail': 'Hiking trail through natural terrain - Forest trail with wooden bridges',
        'desert': 'Arid landscape with unique geology - Eastern Oregon high desert'
    }
    
    print("📸 Stock Photo Acquisition Requirements")
    print("=" * 50)
    print(f"Target: {len(categories)} category-specific images")
    print("Region: Pacific Northwest (Washington/Oregon)")
    print("Style: Outdoor recreation, sunny weather, vibrant colors")
    print("Format: Landscape orientation, 16:9 or 4:3 aspect ratio")
    print("Resolution: Minimum 800x600, ideally 1200x800 or higher")
    
    print("\n🛒 Shopping List:")
    print("-" * 30)
    
    for i, (category, description) in enumerate(categories.items(), 1):
        print(f"{i:2d}. {category.title()}")
        print(f"    Description: {description}")
        print(f"    Keywords: {category}, pacific northwest, outdoor recreation, sunny")
        print(f"    Asset name: {category}.jpg")
        print()
    
    print("💰 Budget Considerations:")
    print("   • Stock photo sites: Shutterstock, Getty, Adobe Stock")
    print("   • Estimated cost: $15-50 per image")
    print(f"   • Total budget: $165-550 for all {len(categories)} images")
    print("   • Alternative: Unsplash Plus subscription ($10/month)")
    
    print("\n🎯 Acquisition Strategy:")
    print("   1. Source highest-priority categories first (mountain, forest, lake)")
    print("   2. Ensure consistent lighting/weather (sunny, clear skies)")
    print("   3. Prefer images with people for activity context")
    print("   4. Verify Pacific Northwest geography when possible")
    
    print("\n📁 Implementation:")
    print("   • Save images to: Frontend/assets/images/categories/")
    print("   • Naming convention: [category].jpg")
    print("   • Update pubspec.yaml assets list") 
    print("   • Test with LocationImageService.getCategoryAssetPath()")
    
    return categories

if __name__ == "__main__":
    categories = generate_photo_requirements()
    
    # Generate a quick test
    print("\n🧪 Quick Test:")
    print("Once images are added, test with:")
    print("   flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000")
    print("   Check that location cards show local images instead of external URLs")
