---
name: webpage_read
agent: CodeActAgent
triggers:
- http://
- https://
---

To read content from a webpage, you can use the `percollate` CLI tool:

1. Install `percollate` with `npm install -g percollate`
2. Once installed, use it to convert a webpage to markdown with the following command:

```bash
percollate md https://example.com --output example.md
```

3. Then, you can read the markdown file `./example.md` using other tools you have access to.
4. If you need to interact further with the webpage, you should not use the `percollate` CLI tool. Instead, you should use the web browser directly provided to you.
