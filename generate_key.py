import secrets
import base64

# Generate a secure random key
def generate_jwt_secret():
    # Generate 32 random bytes and encode them in base64
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

if __name__ == "__main__":
    secret_key = generate_jwt_secret()
    print("\nGenerated JWT Secret Key:")
    print("=" * 50)
    print(secret_key)
    print("=" * 50)
    print("\nAdd this to your .env file as:")
    print(f"SECRET_KEY={secret_key}")
    print("\nMake sure to keep this key secure and don't share it!") 