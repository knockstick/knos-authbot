<div align="center">
  <a href="https://github.com/knockstick/knos-authbot">
    <img src="https://media.discordapp.net/attachments/872388362160455693/1231498864926916649/logo.png?ex=66372db1&is=6624b8b1&hm=bbecdf5c8bd5af7632622b82586a98bf19dd5975a82e3733f6488cee94bed7ef&=&format=webp&quality=lossless" alt="Logo" style="width: 60%; height: 60%;">
  </a>
  
  <h2 align="center">Making a template page</h2>
</div>

1. Create a file named "index.html"
2. Fill it with the content. **This page will be visible to everyone, after they will verify.**
3. If you got some image files, put it in the [`/static/`](https://github.com/knockstick/knos-authbot/tree/main/static) folder. 
4. Add the image files using `{{ url_for('static', 'your_image.png') }}`
5. Done!

```html
<div class="box">
  <img src="{{ url_for('static', filename='my-image.png') }}" alt="Image">
  <p id="success-title">Successfully verified!</p>
  <h2 id="subtitle">You can now close this page.</h2>
</div>
```
---

