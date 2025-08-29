def encrypt(text, shift):
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) - 65 + shift) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) - 97 + shift) % 26 + 97)
        else:
            result += char
    return result

def decrypt(text, shift):
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) - 65 - shift) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) - 97 - shift) % 26 + 97)
        else:
            result += char
    return result

text = input("Enter password ")
shift = int(input("Enter number of shifts "))
print("Text: "+text)
print("Shift: "+str(shift))
encrypted_text = encrypt(text, shift)
print("Encrypted Cipher: ", encrypted_text)
print("Decrypted Cipher: ", decrypt(encrypted_text, shift))
