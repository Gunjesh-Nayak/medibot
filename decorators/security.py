from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac

def validate_signature(payload_bytes, signature_header):
    
    """
    Validate the incoming payload's signature against our expected signature
    """
    # 1. Handle the "sha256=" prefix safely
    if signature_header.startswith("sha256="):
        signature_to_check = signature_header.split("sha256=")[1]
    else:
        # Some providers might send just the hash, or you might want to fail here
        signature_to_check = signature_header

    # 2. Use the App Secret to hash the payload
    # Ensure your secret is encoded correctly (usually utf-8, not latin-1)
    secret_bytes = bytes(current_app.config["APP_SECRET"], "utf-8")
    # secret_bytes = bytes.fromhex(current_app.config["APP_SECRET"])
    
    
    expected_signature = hmac.new(
        secret_bytes,
        msg=payload_bytes, # payload_bytes must be raw bytes!
        digestmod=hashlib.sha256,
    ).hexdigest()

    # 3. Check if the signature matches
    return hmac.compare_digest(expected_signature, signature_to_check)


def signature_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        
        # 1. Capture what Flask sees in the body
        body_bytes = request.get_data()
        
        # 2. Capture what is in the URL (just in case)
        query_bytes = request.query_string
        
        # --- DIAGNOSTIC LOGGING START ---
        print("\n--- DEBUGGING SIGNATURE MISMATCH ---")
        print(f"1. Header Received:   {signature_header}")
        print(f"2. Body Bytes (Hex):  {body_bytes.hex()}")
        print(f"3. Query Bytes (Hex): {query_bytes.hex()}")
        
        # Check what we are actually validating
        if len(body_bytes) == 0 and len(query_bytes) > 0:
            print(">>> WARNING: Body is empty but Query String has data.")
            print(">>> Your signature likely signs the URL, but code validates the Body.")
        # --- DIAGNOSTIC LOGGING END ---
        

        # The validation call
        if not validate_signature(body_bytes, signature_header):
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
            
        return f(*args, **kwargs)


    return decorated_function
# import hmac
# import hashlib

# # 1. Your APP_SECRET
# secret = "APP_SECRET" 

# # 2. The EXACT body from your logs (Note: No space after the colon!)
# payload = ' {"msg":"What are the symptoms of fever?"}'

# # 3. Calculate HMAC
# # Ensure secret is encoded as utf-8 (standard string)
# secret_bytes = secret.encode('utf-8') 

# signature = hmac.new(
#     secret_bytes,
#     msg=payload.encode("utf-8"),
#     digestmod=hashlib.sha256
# ).hexdigest()

# print("--- NEW HEADERS ---")
# print(f"X-Hub-Signature-256: sha256={signature}")