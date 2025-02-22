import http.client

conn = http.client.HTTPSConnection("google-lens-image-search1.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "8ff286b609msh624cda40cb7ff8bp162180jsne1545ee9b080",
    'x-rapidapi-host': "google-lens-image-search1.p.rapidapi.com"
}

conn.request("GET", "/api/v1/google-lens/search/?query_url=https%3A%2F%2Fvokkawprskbismmnczhe.supabase.co%2Fstorage%2Fv1%2Fobject%2Fpublic%2Fpush%2F%2FScreenshot%25202025-02-22%2520at%25207.54.18%2520PM.png", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))