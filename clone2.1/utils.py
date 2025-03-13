import os
import numpy as np
from PIL import Image
import base64
from ecies.utils import generate_eth_key
from ecies import encrypt, decrypt
import hashlib
import zlib
import uuid

# Directory paths
UPLOAD_FOLDER = 'app/static/uploads'
ENCODED_FOLDER = 'app/static/encoded'

# Make sure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCODED_FOLDER, exist_ok=True)

# Get keys from files
def get_ecc_keys():
    with open("pri.key", 'r') as f:
        public_key = f.read()
    
    with open("pvt.key", 'r') as f:
        private_key = f.read()
        
    return private_key, public_key

# ECC encryption function
def ecc_encrypt(plain_text, public_key):
    return encrypt(public_key, plain_text)

# ECC decryption function
def ecc_decrypt(encrypted_data, private_key):
    return decrypt(private_key, encrypted_data)

# Encode function - hides message in image and returns SHA hash
def encode_image(src_path, message, user_id):
    # Generate a unique filename for the encoded image
    filename = f"{user_id}_{uuid.uuid4().hex}.png"
    output_path = os.path.join(ENCODED_FOLDER, filename)
    
    # Open the image
    img = Image.open(src_path, 'r')
    width, height = img.size
    array = np.array(list(img.getdata()))
    
    # Determine number of channels
    if img.mode == 'RGB':
        n = 3
    elif img.mode == 'RGBA':
        n = 4
    else:
        n = 3  # Default to RGB
        img = img.convert('RGB')
        
    total_pixels = array.size // n
    
    # Encode message
    message = message.encode()
    private_key, public_key = get_ecc_keys()
    ecc_encrypt_data = ecc_encrypt(message, public_key)
    
    # Generate SHA hash
    sha = hashlib.sha256(ecc_encrypt_data)
    sender_sha = sha.hexdigest()
    
    # Base64 encode the encrypted data
    message_to_hide = base64.b64encode(ecc_encrypt_data).decode()
    
    # Convert message to binary
    binary_message = ''.join([format(ord(i), "08b") for i in message_to_hide])
    
    # Check if image is large enough
    req_pixels = len(binary_message)
    if req_pixels > total_pixels:
        raise ValueError("Image is too small to hide the message")
    
    # Hide the binary message in the LSB of each pixel
    index = 0
    for p in range(total_pixels):
        for q in range(0, 3):
            if index < req_pixels:
                array[p][q] = int(bin(array[p][q])[2:9] + binary_message[index], 2)
                index += 1
    
    # Reshape array and save the encoded image
    array = array.reshape(height, width, n)
    enc_img = Image.fromarray(array.astype('uint8'), img.mode)
    enc_img.save(output_path)
    
    # Compress the encoded image
    with open(output_path, "rb") as file:
        data = file.read()
    
    compressed_data = zlib.compress(data)
    
    with open(output_path, "wb") as file:
        file.write(compressed_data)
    
    return filename, sender_sha

# Decode function - extracts hidden message from image
def decode_image(src_path):
    # Create a temporary file for the decompressed image
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4().hex}.png")
    
    # Decompress the image
    with open(src_path, "rb") as file:
        data = file.read()
    
    try:
        decompressed_data = zlib.decompress(data)
        
        with open(temp_path, "wb") as file:
            file.write(decompressed_data)
        
        # Open the decompressed image
        img = Image.open(temp_path, 'r')
        array = np.array(list(img.getdata()))
        
        if img.mode == 'RGB':
            n = 3
        elif img.mode == 'RGBA':
            n = 4
        else:
            n = 3
            
        total_pixels = array.size // n
        
        # Extract hidden bits
        hidden_bits = ""
        for p in range(total_pixels):
            for q in range(0, 3):
                hidden_bits += (bin(array[p][q])[2:][-1])
        
        # Group bits into bytes
        hidden_bytes = [hidden_bits[i:i+8] for i in range(0, len(hidden_bits), 8)]
        
        # Convert bytes to characters
        message = ""
        for i in range(len(hidden_bytes)):
            if i < len(hidden_bytes):
                message += chr(int(hidden_bytes[i], 2))
        
        # Base64 decode and decrypt
        try:
            ecc_encrypt_data = base64.b64decode(message.encode())
            
            # Generate SHA hash for verification
            sha = hashlib.sha256(ecc_encrypt_data)
            sha_hash = sha.hexdigest()
            
            # Decrypt the message
            private_key, public_key = get_ecc_keys()
            decrypted = ecc_decrypt(ecc_encrypt_data, private_key)
            
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return decrypted.decode(), sha_hash
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"Failed to decode message: {str(e)}")
            
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise ValueError(f"Failed to decompress image: {str(e)}")