import xai_sdk

client = xai_sdk.Client()

response = client.image.sample(
    prompt="A collage of London landmarks in a stenciled street‑art style",
    model="grok-imagine-image",
)

print(response.url)
