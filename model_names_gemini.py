import google.generativeai as genai

# API Anahtarını buraya yaz
genai.configure(api_key="AIzaSyBwkUTQeif-Z-2xeNWkixJh-yrVkoaKzcI")

print("Mevcut Modeller:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")