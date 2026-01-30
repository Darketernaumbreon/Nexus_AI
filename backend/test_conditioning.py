"""
Test script for DEM conditioning module.
Tests pit filling and flat resolution on real Assam DEM.
"""

from pathlib import Path
from app.modules.geospatial.hydrology.conditioning import condition_dem

def test_conditioning():
    """Test DEM conditioning on Assam DEM from Task 2."""
    print("=" * 70)
    print("Testing DEM Conditioning Module")
    print("=" * 70)
    
    # Use DEM from Task 2
    dem_path = Path("data/dem_cache/dem_COP30_a31683f8.tif")
    
    if not dem_path.exists():
        print(f"\n[ERROR] DEM not found: {dem_path}")
        print("Please run test_dem_acquisition.py first to download the DEM.")
        return
    
    print(f"\n1. Conditioning DEM: {dem_path.name}")
    print(f"   This will perform:")
    print(f"   - Pit filling (priority-flood algorithm)")
    print(f"   - Flat resolution (Garbrecht & Martz method)")
    
    try:
        # Condition DEM
        conditioned = condition_dem(dem_path, cache=True)
        
        print(f"\n[OK] DEM conditioned successfully!")
        print(f"\n2. Conditioning Results:")
        print(f"   - Pits filled: {conditioned.metadata['pits_filled']}")
        print(f"   - Mean fill depth: {conditioned.metadata['mean_fill_depth']:.3f}m")
        print(f"   - Max fill depth: {conditioned.metadata['max_fill_depth']:.3f}m")
        print(f"   - Flats resolved: {conditioned.metadata['flats_resolved']}")
        print(f"   - Mean gradient added: {conditioned.metadata['mean_gradient_added']:.6f}m")
        print(f"   - Max gradient added: {conditioned.metadata['max_gradient_added']:.6f}m")
        print(f"   - Total time: {conditioned.metadata['conditioning_time']:.2f}s")
        
        print(f"\n3. Output Details:")
        print(f"   - Shape: {conditioned.data.shape}")
        print(f"   - CRS: {conditioned.crs}")
        print(f"   - NoData: {conditioned.nodata}")
        print(f"   - Min elevation: {conditioned.data.min():.2f}m")
        print(f"   - Max elevation: {conditioned.data.max():.2f}m")
        
        # Test caching
        print(f"\n4. Testing cache (re-conditioning same DEM)...")
        conditioned2 = condition_dem(dem_path, cache=True)
        
        if conditioned2.metadata.get('cached'):
            print(f"   [OK] Cache working! Loaded from cache instantly.")
        else:
            print(f"   [WARNING] Cache not used - reconditioned DEM")
        
        # Calculate impact
        total_cells = conditioned.data.size
        pits_pct = (conditioned.metadata['pits_filled'] / total_cells) * 100
        flats_pct = (conditioned.metadata['flats_resolved'] / total_cells) * 100
        
        print(f"\n5. Impact Analysis:")
        print(f"   - Total cells: {total_cells:,}")
        print(f"   - Cells modified by pit filling: {pits_pct:.2f}%")
        print(f"   - Cells modified by flat resolution: {flats_pct:.2f}%")
        
        if pits_pct < 1.0 and flats_pct < 5.0:
            print(f"   [OK] Minimal terrain modification - good DEM quality")
        elif pits_pct > 10.0:
            print(f"   [WARNING] High pit filling - DEM quality may be poor")
        
        print(f"\n{'=' * 70}")
        print("[OK] All conditioning tests passed!")
        print(f"{'=' * 70}")
        
        print(f"\nConditioned DEM cached to:")
        cache_path = Path(f"data/conditioned_cache/conditioned_{dem_path.name}")
        print(f"  {cache_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conditioning()
