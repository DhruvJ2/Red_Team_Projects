# Create ROT13 translation table
rot13 = str.maketrans(
    'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
    'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm'
)

def encrypt(text):
    return text.translate(rot13)

def decrypt(text):
    # ROT13 encryption is symmetric so decrypt is same as encrypt
    return text.translate(rot13)

text = input('Enter text:\n> ')
ciphertext = encrypt(text)
print(f"Your cipher text is: {ciphertext}")

plaintext = decrypt(ciphertext)
print(f"Decrypted text is: {plaintext}")

