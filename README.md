# autogen

"uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "6100"

```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 6100 > /root/logs/autogen/access.log 2>&1 &
```
