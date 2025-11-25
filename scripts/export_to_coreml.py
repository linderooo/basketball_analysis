#!/usr/bin/env python3
"""
Export YOLO models to CoreML format for Apple Neural Engine (ANE) acceleration.
"""

from ultralytics import YOLO
import os

def export_model(model_path):
    """Export a YOLO model to CoreML format."""
    print(f"\n{'='*60}")
    print(f"Exporting: {model_path}")
    print(f"{'='*60}")
    
    try:
        # Load YOLO model
        model = YOLO(model_path)
        
        # Export to CoreML with NMS included
        # imgsz=640 is the standard YOLO input size
        success = model.export(
            format='coreml',
            nms=True,  # Include Non-Maximum Suppression in the model
            imgsz=640
        )
        
        output_path = model_path.replace('.pt', '.mlpackage')
        print(f"✅ Successfully exported to: {output_path}")
        
        # Check file size
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"📦 CoreML package size: {size_mb:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Export all YOLO models to CoreML."""
    models_to_export = [
        'models/player_detector.pt',
        'models/ball_detector_model.pt',
        'models/court_keypoint_detector.pt'
    ]
    
    print("\n🍎 YOLO to CoreML Converter for Apple Neural Engine")
    print("This will create .mlpackage files optimized for M3 hardware\n")
    
    results = {}
    for model_path in models_to_export:
        if not os.path.exists(model_path):
            print(f"⚠️  Skipping {model_path} - file not found")
            results[model_path] = False
            continue
        
        results[model_path] = export_model(model_path)
    
    # Summary
    print(f"\n{'='*60}")
    print("EXPORT SUMMARY")
    print(f"{'='*60}")
    
    for model_path, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {os.path.basename(model_path)}")
    
    successful = sum(results.values())
    total = len(results)
    
    print(f"\nCompleted: {successful}/{total} models exported successfully")
    
    if successful == total:
        print("\n🎉 All models ready for Apple Neural Engine!")
        print("Next steps:")
        print("1. The code will automatically use .mlpackage files")
        print("2. Run your analysis to see the speedup")
        print("3. Monitor ANE usage with: sudo powermetrics --samplers ane")

if __name__ == '__main__':
    main()
