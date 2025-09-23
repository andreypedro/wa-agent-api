#!/usr/bin/env python3
"""
Test the intelligent validation error recovery system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_phone_auto_correction():
    """Test automatic phone number correction"""
    session_id = "test_validation_recovery"

    print("=== Testing Intelligent Validation Error Recovery ===")

    # Create workflow
    workflow = get_lead_conversion_workflow(session_id=session_id)

    # Test various phone number formats that should be auto-corrected
    test_cases = [
        ("988919158", "11988919158"),  # 9 digits -> add area code
        ("88919158", "1188919158"),   # 8 digits -> add area code + 9
        ("9988919158", "11988919158"), # 10 digits starting with 9 -> add area code
        ("1188919158", "1188919158"),  # 11 digits -> keep as is
        ("551188919158", "1188919158"), # 12 digits with country code -> remove country code
    ]

    print("\n1. Testing phone number auto-correction:")
    for original, expected in test_cases:
        fixed = workflow._try_fix_phone_number(original)
        status = "✅" if fixed == expected else "❌"
        print(f"   {status} {original} → {fixed} (expected: {expected})")

    # Test validation with auto-correction
    print("\n2. Testing validation with auto-correction:")
    test_data = {"telefone": "988919158"}  # 9 digits, should be auto-corrected
    fixed_data, issues = workflow._validate_and_fix_data(test_data, "988919158")

    if not issues and "telefone" in fixed_data:
        print(f"   ✅ Successfully auto-corrected: 988919158 → {fixed_data['telefone']}")
    else:
        print(f"   ❌ Auto-correction failed: {issues}")

    # Test corrupted session recovery
    print("\n3. Testing corrupted session recovery:")

    # Manually corrupt the session with invalid phone
    workflow.session_state["context"]["lead_data"]["telefone"] = "123"  # Invalid phone

    try:
        context = workflow._get_context()
        phone = context.lead_data.telefone
        if phone is None:
            print("   ✅ Successfully removed invalid phone number")
        elif len(phone) >= 10:
            print(f"   ✅ Successfully fixed phone number: 123 → {phone}")
        else:
            print(f"   ❌ Phone still invalid: {phone}")
    except Exception as e:
        print(f"   ❌ Session recovery failed: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_phone_auto_correction()