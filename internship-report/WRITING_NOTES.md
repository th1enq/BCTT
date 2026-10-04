# Skills và nguyên tắc biên soạn

Ngày áp dụng: 04/10/2026. Ngôn ngữ báo cáo là tiếng Việt theo yêu cầu người dùng.

## Skills tìm được và đã áp dụng

1. **academic-writing** từ [YuanZHAO321/Academic-Writing](https://github.com/YuanZHAO321/Academic-Writing). Bản tải tại `report-skills/academic-writing/`. Đã đọc toàn bộ SKILL.md và các tài liệu bắt buộc cho tác vụ: `structure.md`, `style.md`, `figures-tables.md`, `revision-submission.md`.
2. **pdf** từ [openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/pdf). Bản tải tại `report-skills/pdf/`. Áp dụng kiểm tra PDF bằng kết xuất từng trang, kiểm tra chữ, công thức, bảng và bố cục trước bàn giao.
3. **skill-installer** có sẵn được dùng để khảo sát danh mục và tải hai bộ kỹ năng vào dự án. Đây là bước hỗ trợ tìm kiếm, không phải skill viết học thuật.

Các bản tải được lưu ở dự án, không đăng ký hoặc thay đổi cấu hình skills toàn cục. Chúng được dùng làm tài liệu hướng dẫn trực tiếp trong lần biên soạn này. Yêu cầu tiếng Việt và dùng LaTeX UET của người dùng có ưu tiên hơn các mặc định tiếng Anh hoặc ReportLab trong skill.

## Ảnh hưởng cụ thể đến bản báo cáo

- Tóm tắt và kết luận nêu đóng góp, phạm vi và kết quả định lượng ngay, không chờ đến chương cài đặt.
- Trình bày theo câu hỏi → mô hình → thuật toán → bằng chứng → giới hạn; mỗi đoạn có một nhiệm vụ lập luận.
- Tách kiến thức nền khỏi đóng góp của đề tài: tổng tiền tố, tô-pô, Tarjan không được nhận là kỹ thuật mới do đề tài phát minh.
- Nêu điều kiện truy vấn cực–cực của TTSP, phân biệt với truy vấn tùy ý và partial 2-tree.
- Phân biệt phép toán số học, tiền xử lý và chi phí bit; định nghĩa nhất quán `n,m,M,r,w,N,B`.
- Tính lại bảng từ CSV đã kiểm tra, không chép số bằng tay. GM chỉ từ cặp hoàn thành; trường hợp hết giờ/bỏ qua được ghi nhận.
- Chỉ so sánh với paper trên phạm vi thực sự có đối chứng tương ứng. Mức tăng tốc đối chứng nội bộ không biến thành tuyên bố nhanh hơn chương trình của tác giả paper.
- Ghi rõ phạm vi vét cạn, dữ liệu sinh, tần số CPU, số mẫu và nhu cầu thẩm định độc lập. Không tự gán điểm, không bảo đảm xếp loại, không tuyên bố tính mới toàn cầu.
- Để trống thông tin thực tập chưa được cung cấp và trang nhận xét; không dùng tên hoặc năm giả từ mẫu.
- Giữ nguyên lớp UET và bản khóa luận cũ; chỉ thêm lớp tương thích phông chữ ở điểm vào báo cáo.

## Đối chiếu bố cục mẫu

| Yêu cầu của template.pdf | Phần trong báo cáo |
|---|---|
| Giới thiệu công việc, bài toán | Chương 1 |
| Yêu cầu và phần việc thực hiện | Chương 2 và Mục 1.2 |
| Lý thuyết cần thiết, giải pháp, thuật toán | Chương 3 |
| Mô tả phần mềm nếu có | Không đưa vào, theo yêu cầu bỏ chi tiết implement |
| Kết quả, kiến thức, hướng phát triển | Chương 4–5 |
| Lời cảm ơn, tài liệu tham khảo, nhận xét | Các trang riêng tương ứng |

## Nguồn chính kiểm tra khi viết

- Enright, Meeks, Molter (2025): [Counting Temporal Paths](https://doi.org/10.1007/s00453-025-01301-3), đặc biệt kết quả về rừng và câu hỏi series–parallel trong kết luận.
- Eppstein (1992): [trang công bố của tác giả](https://ics.uci.edu/~eppstein/pubs/j-ic.html), định nghĩa và phân rã TTSP.
- Tarjan (1972): [bài gốc SIAM](https://doi.org/10.1137/0201010), phân rã thành phần hai-liên-thông bằng DFS.
- [NetworkX Graph Atlas](https://networkx.org/documentation/stable/reference/generated/networkx.generators.atlas.graph_atlas_g.html): quy mô và nguồn bộ đồ thị nhỏ; bản dữ liệu dự án lấy từ NetworkX 3.5.
- Nguồn dự án: `results/research_highlights.json`, `research_audit_summary.json`, hai CSV benchmark cuối, metadata và các chứng minh ở `thesis/chapters/`.
