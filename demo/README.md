# Demo — Plausibility Pretesting

Web demo chấm độ hợp lý (plausibility) câu tiếng Anh thang **1–7** bằng **`gpt-5.6-luna`**, dùng prompt paper `mem_enc` (few-shot).

Mỗi dòng trong ô nhập = một câu. Câu có trong dataset `mem_enc` sẽ hiện thêm `human_mean`.

---

## Yêu cầu

- Python 3.10+
- API key OpenAI trong `doan/.env`:

```bash
OPENAI_API_KEY=sk-...
```

File `.env` nằm ở thư mục `doan/` (cùng cấp với `demo/`), **không** commit lên git.

---

## Cài đặt

Từ thư mục gốc repo (hoặc bất kỳ đâu), tạo/ kích hoạt venv rồi cài dependency:

```bash
# Ví dụ: venv ở root repo
cd /path/to/CS2202.CH202
python3 -m venv venv
source venv/bin/activate

pip install -r doan/requirements-eval.txt
```

---

## Chạy

```bash
source /path/to/CS2202.CH202/venv/bin/activate
cd doan/demo
python app.py
```

Mở trình duyệt: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Hoặc dùng uvicorn trực tiếp:

```bash
cd doan/demo
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

## Cách dùng nhanh

1. Nhập 1 hoặc nhiều câu (mỗi câu một dòng), bấm **Chấm điểm**.
2. Click một chip câu mẫu → chấm ngay câu đó.
3. Click **Nhiều câu … — chạy hết** (hoặc **Chạy tất cả mẫu**) → đổ hết câu mẫu rồi chấm hàng loạt.
4. `Ctrl/Cmd + Enter` trong textarea cũng gửi request.

---

## Biến môi trường (tuỳ chọn)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `OPENAI_API_KEY` | (bắt buộc) | Key gọi OpenAI |
| `DEMO_MODEL` | `gpt-5.6-luna` | Model name |
| `DEMO_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `DEMO_TEMPERATURE` | `1.0` | Temperature (GPT-5.x realtime thường chỉ nhận 1.0) |
| `DEMO_MAX_TOKENS` | `128` | `max_completion_tokens` |
| `DEMO_MAX_SENTENCES` | `20` | Số câu tối đa / request |
| `DEMO_MAX_WORKERS` | `4` | Số worker song song khi chấm nhiều câu |
| `PORT` | `8000` | Cổng server |

Ví dụ đổi model / port:

```bash
DEMO_MODEL=gpt-5.6-luna PORT=8001 python app.py
```

---

## Kiểm tra API nhanh

```bash
curl -s http://127.0.0.1:8000/api/health

curl -s -X POST http://127.0.0.1:8000/api/score \
  -H 'Content-Type: application/json' \
  -d '{"text":"The teacher scolded the shoe.\nThe nurse fetched the patient."}'
```

---

## Cấu trúc

```text
doan/demo/
├── README.md          # file này
├── app.py             # FastAPI backend
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

Prompt / parse score tái sử dụng `doan/src/plausibility_eval/`.
