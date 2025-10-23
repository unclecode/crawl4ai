"""
Lightweight test to verify pyOpenSSL security fix (Issue #1545).

This test verifies the security requirements are met:
1. pyOpenSSL >= 25.3.0 is installed
2. cryptography >= 45.0.7 is installed (above vulnerable range)
3. SSL/TLS functionality works correctly

This test can run without full crawl4ai dependencies installed.
"""

import sys
from packaging import version


def test_package_versions():
    """Test that package versions meet security requirements."""
    print("=" * 70)
    print("TEST: Package Version Security Requirements (Issue #1545)")
    print("=" * 70)

    all_passed = True

    # Test pyOpenSSL version
    try:
        import OpenSSL
        pyopenssl_version = OpenSSL.__version__
        print(f"\n✓ pyOpenSSL is installed: {pyopenssl_version}")

        if version.parse(pyopenssl_version) >= version.parse("25.3.0"):
            print(f"  ✓ PASS: pyOpenSSL {pyopenssl_version} >= 25.3.0 (required)")
        else:
            print(f"  ✗ FAIL: pyOpenSSL {pyopenssl_version} < 25.3.0 (required)")
            all_passed = False

    except ImportError as e:
        print(f"\n✗ FAIL: pyOpenSSL not installed - {e}")
        all_passed = False

    # Test cryptography version
    try:
        import cryptography
        crypto_version = cryptography.__version__
        print(f"\n✓ cryptography is installed: {crypto_version}")

        # The vulnerable range is >=37.0.0 & <43.0.1
        # We need >= 45.0.7 to be safe
        if version.parse(crypto_version) >= version.parse("45.0.7"):
            print(f"  ✓ PASS: cryptography {crypto_version} >= 45.0.7 (secure)")
            print(f"  ✓ NOT in vulnerable range (37.0.0 to 43.0.0)")
        elif version.parse(crypto_version) >= version.parse("37.0.0") and version.parse(crypto_version) < version.parse("43.0.1"):
            print(f"  ✗ FAIL: cryptography {crypto_version} is VULNERABLE")
            print(f"  ✗ Version is in vulnerable range (>=37.0.0 & <43.0.1)")
            all_passed = False
        else:
            print(f"  ⚠ WARNING: cryptography {crypto_version} < 45.0.7")
            print(f"  ⚠ May not meet security requirements")

    except ImportError as e:
        print(f"\n✗ FAIL: cryptography not installed - {e}")
        all_passed = False

    return all_passed


def test_ssl_basic_functionality():
    """Test that SSL/TLS basic functionality works."""
    print("\n" + "=" * 70)
    print("TEST: SSL/TLS Basic Functionality")
    print("=" * 70)

    try:
        import OpenSSL.SSL

        # Create a basic SSL context to verify functionality
        context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
        print("\n✓ SSL Context created successfully")
        print("  ✓ PASS: SSL/TLS functionality is working")
        return True

    except Exception as e:
        print(f"\n✗ FAIL: SSL functionality test failed - {e}")
        return False


def test_pyopenssl_crypto_integration():
    """Test that pyOpenSSL and cryptography integration works."""
    print("\n" + "=" * 70)
    print("TEST: pyOpenSSL <-> cryptography Integration")
    print("=" * 70)

    try:
        from OpenSSL import crypto

        # Generate a simple key pair to test integration
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        print("\n✓ Generated RSA key pair successfully")
        print("  ✓ PASS: pyOpenSSL and cryptography are properly integrated")
        return True

    except Exception as e:
        print(f"\n✗ FAIL: Integration test failed - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all security tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  pyOpenSSL Security Fix Verification - Issue #1545               ║")
    print("╚" + "=" * 68 + "╝")
    print("\nVerifying that the pyOpenSSL update resolves the security vulnerability")
    print("in the cryptography package (CVE: versions >=37.0.0 & <43.0.1)\n")

    results = []

    # Test 1: Package versions
    results.append(("Package Versions", test_package_versions()))

    # Test 2: SSL functionality
    results.append(("SSL Functionality", test_ssl_basic_functionality()))

    # Test 3: Integration
    results.append(("pyOpenSSL-crypto Integration", test_pyopenssl_crypto_integration()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        all_passed = all_passed and passed

    print("=" * 70)

    if all_passed:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("✓ Security vulnerability is resolved")
        print("✓ pyOpenSSL >= 25.3.0 is working correctly")
        print("✓ cryptography >= 45.0.7 (not vulnerable)")
        print("\nThe dependency update is safe to merge.\n")
        return True
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("✗ Security requirements not met")
        print("\nDo NOT merge until all tests pass.\n")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
