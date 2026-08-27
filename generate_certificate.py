"""
generate_certificate.py
Standalone CLI entry point for generating the MRPL Sovereign AI Cryptographic Proof-of-Execution Certificate.

Usage:
    python generate_certificate.py

Outputs:
    deliverables/MRPL_Proof_of_Execution_Certificate.png
    deliverables/MRPL_Proof_of_Execution_Certificate.pdf
    deliverables/certificate.png
    deliverables/certificate.pdf
"""

from harness.certificate_generator import generate_certificate

if __name__ == "__main__":
    res = generate_certificate()
    print("\n" + "=" * 70)
    print("  MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL)")
    print("  SOVEREIGN AI - PROOF-OF-EXECUTION CERTIFICATE GENERATED")
    print("=" * 70)
    print(f"  • Certificate ID : {res['certificate_id']}")
    print(f"  • Merkle Root    : {res['root_hash']}")
    print(f"  • Output PNG     : {res['png_path']}")
    print(f"  • Output PDF     : {res['pdf_path']}")
    print("=" * 70)
