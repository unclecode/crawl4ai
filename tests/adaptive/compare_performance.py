"""
Compare performance before and after optimizations
"""

def read_baseline():
    """Read baseline performance metrics"""
    with open('performance_baseline.txt', 'r') as f:
        content = f.read()
    
    # Extract key metrics
    metrics = {}
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Total Time:' in line:
            metrics['total_time'] = float(line.split(':')[1].strip().split()[0])
        elif 'Memory Used:' in line:
            metrics['memory_mb'] = float(line.split(':')[1].strip().split()[0])
        elif 'validate_coverage:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['validate_coverage_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])
        elif 'select_links:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['select_links_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])
        elif 'calculate_confidence:' in line and i+1 < len(lines) and 'Avg Time:' in lines[i+2]:
            metrics['calculate_confidence_ms'] = float(lines[i+2].split(':')[1].strip().split()[0])
            
    return metrics


def print_comparison(before_metrics, after_metrics):
    """Print performance comparison"""
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON: BEFORE vs AFTER OPTIMIZATIONS")
    print("="*80)
    
    # Total time
    time_improvement = (before_metrics['total_time'] - after_metrics['total_time']) / before_metrics['total_time'] * 100
    print(f"\n📊 Total Time:")
    print(f"   Before: {before_metrics['total_time']:.2f} seconds")
    print(f"   After:  {after_metrics['total_time']:.2f} seconds")
    print(f"   Improvement: {time_improvement:.1f}% faster ✅" if time_improvement > 0 else f"   Slower: {-time_improvement:.1f}% ❌")
    
    # Memory
    mem_improvement = (before_metrics['memory_mb'] - after_metrics['memory_mb']) / before_metrics['memory_mb'] * 100
    print(f"\n💾 Memory Usage:")
    print(f"   Before: {before_metrics['memory_mb']:.2f} MB")
    print(f"   After:  {after_metrics['memory_mb']:.2f} MB")
    print(f"   Improvement: {mem_improvement:.1f}% less memory ✅" if mem_improvement > 0 else f"   More memory: {-mem_improvement:.1f}% ❌")
    
    # Key operations
    print(f"\n⚡ Key Operations:")
    
    # Validate coverage
    if 'validate_coverage_ms' in before_metrics and 'validate_coverage_ms' in after_metrics:
        val_improvement = (before_metrics['validate_coverage_ms'] - after_metrics['validate_coverage_ms']) / before_metrics['validate_coverage_ms'] * 100
        print(f"\n   validate_coverage:")
        print(f"     Before: {before_metrics['validate_coverage_ms']:.1f} ms")
        print(f"     After:  {after_metrics['validate_coverage_ms']:.1f} ms")
        print(f"     Improvement: {val_improvement:.1f}% faster ✅" if val_improvement > 0 else f"     Slower: {-val_improvement:.1f}% ❌")
    
    # Select links
    if 'select_links_ms' in before_metrics and 'select_links_ms' in after_metrics:
        sel_improvement = (before_metrics['select_links_ms'] - after_metrics['select_links_ms']) / before_metrics['select_links_ms'] * 100
        print(f"\n   select_links:")
        print(f"     Before: {before_metrics['select_links_ms']:.1f} ms")
        print(f"     After:  {after_metrics['select_links_ms']:.1f} ms")
        print(f"     Improvement: {sel_improvement:.1f}% faster ✅" if sel_improvement > 0 else f"     Slower: {-sel_improvement:.1f}% ❌")
    
    # Calculate confidence
    if 'calculate_confidence_ms' in before_metrics and 'calculate_confidence_ms' in after_metrics:
        calc_improvement = (before_metrics['calculate_confidence_ms'] - after_metrics['calculate_confidence_ms']) / before_metrics['calculate_confidence_ms'] * 100
        print(f"\n   calculate_confidence:")
        print(f"     Before: {before_metrics['calculate_confidence_ms']:.1f} ms")
        print(f"     After:  {after_metrics['calculate_confidence_ms']:.1f} ms")
        print(f"     Improvement: {calc_improvement:.1f}% faster ✅" if calc_improvement > 0 else f"     Slower: {-calc_improvement:.1f}% ❌")
    
    print("\n" + "="*80)
    
    # Overall assessment
    if time_improvement > 50:
        print("🎉 EXCELLENT OPTIMIZATION! More than 50% performance improvement!")
    elif time_improvement > 30:
        print("✅ GOOD OPTIMIZATION! Significant performance improvement!")
    elif time_improvement > 10:
        print("👍 DECENT OPTIMIZATION! Noticeable performance improvement!")
    else:
        print("🤔 MINIMAL IMPROVEMENT. Further optimization may be needed.")
    
    print("="*80)


if __name__ == "__main__":
    # Example usage - you'll run this after implementing optimizations
    baseline = read_baseline()
    print("Baseline metrics loaded:")
    for k, v in baseline.items():
        print(f"  {k}: {v}")
    
    print("\n⚠️  Run the performance test again after optimizations to compare!")
    print("Then update this script with the new metrics to see the comparison.")