import urllib.request
import json

def test_full_pipeline():
    with open("jarvis_custom_test.csv", "r", encoding="utf-8") as f:
        csv_text = f.read()

    # 1. Validation
    req_val = urllib.request.Request(
        "http://127.0.0.1:8089/api/investigate/validate",
        data=json.dumps({"csv_text": csv_text}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_val) as res:
        val = json.loads(res.read().decode("utf-8"))
        print("=== 1. VALIDATION RESULT ===")
        print(f"Total Rows: {val['total_rows']}")
        print(f"Valid Transactions: {val['valid_rows']}")
        print(f"Invalid Rows: {val['invalid_rows']}")
        print(f"Total Volume: Rs. {val['total_volume_inr']:,.2f}")
        print(f"Acceptable: {val['is_acceptable_for_analysis']}")

    # 2. Custom Pipeline
    req_custom = urllib.request.Request(
        "http://127.0.0.1:8089/api/investigate/custom",
        data=json.dumps({
            "csv_text": csv_text,
            "dataset_name": "JARVIS Custom Test Case"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_custom) as res:
        case = json.loads(res.read().decode("utf-8"))
        print("\n=== 2. CASE EXECUTION RESULT ===")
        print(f"Case ID: {case['case_id']}")
        print(f"Graph Accounts: {len(case['graph']['nodes'])}")
        print(f"Graph Transactions: {len(case['graph']['edges'])}")
        print(f"Detected Patterns: {len(case['patterns'])}")
        print(f"Attack Paths: {len(case['attack_paths'])}")
        print(f"Dynamic DNA Signature: {case['primary_dna']['signature']}")
        print(f"DNA Integrity SHA256: {case['primary_dna']['evidence_payload_sha256']}")
        print("\nInferred Account Roles:")
        for acc_id, role_info in case['roles'].items():
            print(f"  - {acc_id}: {role_info['probable_role']} (confidence: {role_info['confidence']:.2f})")
        print("\nExecutive Summary:")
        summary_text = case['narrative_brief'].get('executive_summary', '')
        print("Executive Summary:", summary_text.encode('ascii', errors='replace').decode('ascii'))

if __name__ == "__main__":
    test_full_pipeline()
