import requests
from PIL import Image
from transformers import AutoProcessor, BlipForConditionalGeneration

processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

img_path = "image_r.jpg"
image = Image.open(img_path).convert('RGB')

text = "the image of"
inputs = processor(images=image, text=text, return_tensors="pt")

outputs = model.generate(**inputs, max_length=50)

caption = processor.decode(outputs[0], skip_special_tokens=True)

print(caption)