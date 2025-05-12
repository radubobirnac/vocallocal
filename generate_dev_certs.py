from OpenSSL import crypto
import os

# Create ssl directory if it doesn't exist
os.makedirs('ssl', exist_ok=True)

# Generate a key pair
key = crypto.PKey()
key.generate_key(crypto.TYPE_RSA, 2048)

# Create a self-signed cert
cert = crypto.X509()
cert.get_subject().CN = "localhost"
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for a year
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha256')

# Write to disk
with open("ssl/cert.pem", "wb") as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
with open("ssl/key.pem", "wb") as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

print("Self-signed certificates generated in ssl/ directory")
print("Run 'python run_dev_secure.py' to start the server with HTTPS")
key.generate_key(crypto.TYPE_RSA, 2048) 
 
# Create a self-signed cert 
cert = crypto.X509() 
cert.get_subject().CN = "localhost" 
cert.set_serial_number(1000) 
cert.gmtime_adj_notBefore(0) 
cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for a year 
cert.set_issuer(cert.get_subject()) 
cert.set_pubkey(key) 
cert.sign(key, 'sha256') 
 
# Write to disk 
with open("ssl/cert.pem", "wb") as f: 
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert)) 
with open("ssl/key.pem", "wb") as f: 
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key)) 
 
print("Self-signed certificates generated in ssl/ directory") 
