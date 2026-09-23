# Kiến trúc

## Trách nhiệm các dịch vụ

- `MCP-Server` công bố capability qua Streamable HTTP. Ví dụ hiện tại có tool `greet`.
- `AI-Agent` giữ logic điều phối. Nó mở kết nối MCP lúc khởi động, chuyển danh sách tool cho model, chạy tool call qua `ToolNode` rồi tạo câu trả lời.
- PostgreSQL lưu checkpoint của LangGraph. API nhận `thread_id` để tiếp tục hội thoại qua nhiều request.

## StateGraph

`MessagesState` cộng dồn các message. Node `agent` gọi model với system prompt và lịch sử; `tools_condition` chuyển tới node `tools` nếu model yêu cầu tool, hoặc kết thúc lượt. Node `tools` chạy các LangChain tool do MCPAdapter cung cấp rồi quay lại `agent`. `recursion_limit=20` chặn một lượt đi qua graph vô hạn.

## Vòng đời

FastAPI lifespan mở `MCPAdapter` và PostgreSQL checkpointer trước khi nhận request. Nếu MCP hoặc database không sẵn sàng, startup thất bại và `/ready` không trả 200. Khi dừng dịch vụ, các kết nối được đóng qua `AsyncExitStack`.

Graph chỉ dùng tool MCP được tải lúc startup. Nếu danh sách tool trên MCP server thay đổi, khởi động lại agent để tải lại. Agent không tự sử dụng MCP resource/prompt.

## Tách dữ liệu

MCP server và agent là hai package và hai container riêng. Agent chỉ phụ thuộc vào URL MCP; có thể thay server khác cùng giao thức. PostgreSQL chỉ dùng cho lịch sử LangGraph và không thuộc MCP server.
