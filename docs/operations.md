# Vận hành

## Biến môi trường

| Biến | Bắt buộc | Ý nghĩa |
| --- | --- | --- |
| `OPENAI_API_KEY` | Có | Khóa gọi model, giữ trong secret manager |
| `OPENAI_MODEL` | Không | Model có hỗ trợ tool calling; mặc định `gpt-4.1-mini` |
| `MCP_URL` | Không | Endpoint MCP HTTP; mặc định `http://127.0.0.1:8000/mcp` |
| `DATABASE_URL` | Khi cần lưu lịch sử lâu dài | PostgreSQL URL cho LangGraph checkpointer |
| `AGENT_HOST` | Không | Địa chỉ lắng nghe; mặc định `127.0.0.1` |
| `AGENT_PORT` | Không | Cổng HTTP; mặc định `8080` |

## Endpoint

- `GET /health`: HTTP process hoạt động.
- `GET /ready`: MCP tools và graph đã khởi tạo.
- `POST /chat`: body `{"thread_id":"...","message":"..."}`; trả `{"thread_id":"...","answer":"..."}`.
- `GET /docs`: OpenAPI UI của FastAPI, chỉ nên mở trong mạng tin cậy.

## Triển khai thực tế

1. Giữ API sau reverse proxy TLS và xác thực. Compose chỉ bind vào loopback để thử tại máy.
2. Cấp `OPENAI_API_KEY` và `DATABASE_URL` từ secret manager; không commit `.env`.
3. Dùng PostgreSQL có backup, volume bền vững và migration kiểm soát. `checkpointer.setup()` được gọi khi startup.
4. Chạy một instance trước; nếu mở rộng, theo dõi việc nhiều request cùng `thread_id` và quản lý thứ tự gọi từ client.
5. Cấu hình log tập trung, tracing, timeout, giới hạn request và ngân sách model theo hạ tầng của bạn. Hiện source chỉ cung cấp điểm mở rộng cho các phần này.
6. Tạo lock file cho cả dependency trực tiếp và gián tiếp, build/publish image cố định bằng digest, rồi chạy test và kiểm tra tích hợp với MCP trước khi phát hành.

## Sự cố thường gặp

- `/ready` không lên: kiểm tra `docker compose logs agent`, `docker compose logs mcp`, `docker compose logs db`.
- Agent không thấy tool mới: khởi động lại `agent` để MCPAdapter tải danh sách mới.
- Hội thoại mất lịch sử sau restart: kiểm tra `DATABASE_URL`; nếu để trống, checkpointer nằm trong RAM.
- Model không gọi tool: kiểm tra model có hỗ trợ tool calling, mô tả tool MCP và nội dung system prompt.
