# Báo cáo thực tập UET

Báo cáo riêng, không thay thế bản khóa luận trong `thesis/` hoặc `results/temporal_path_thesis.pdf`.
Nội dung tập trung vào bài toán, ý tưởng, thuật toán, lập luận tính đúng, độ phức tạp và kết quả. Không có chương chi tiết cài đặt, mã C++ hoặc hướng dẫn dòng lệnh trong PDF.

## Tệp chính

- `main.tex`: điểm vào biên dịch.
- `metadata.tex`: thông tin cá nhân và thực tập; đã điền Quách Đức Thiện, 23020161, Thạc sĩ Trần Mạnh Cường. Lớp, đơn vị, thời gian thực tập và tháng/năm báo cáo đang để dòng trống.
- `chapters/`: năm chương nội dung.
- `generated/`: bảng, số liệu và bản kê nguồn dữ liệu đã kiểm tra. Những tệp này đi kèm để biên dịch mà không phải chạy lại benchmark.
- `font-compat.tex`: tương thích phông chữ; không sửa lớp UET gốc.
- `WRITING_NOTES.md`: nguồn skills và các nguyên tắc đã áp dụng.

PDF được xuất tới `../output/pdf/bao_cao_thuc_tap_uet.pdf`.
Trang nhận xét, điểm và chữ ký được để trống cho giảng viên đánh giá.
Bản bàn giao hiện tại có **19 trang PDF, trong đó 13 trang nội dung chính**.

Gói `bao_cao_thuc_tap_uet_latex.zip` chứa nguồn và các tài nguyên cần để sửa/biên dịch báo cáo. Việc sinh lại bảng từ dữ liệu nghiên cứu hoặc kiểm tra toàn bộ bản kê cần dự án đầy đủ; không cần chạy các bước đó để biên dịch gói nguồn đã có bảng.

## Biên dịch

Yêu cầu LuaLaTeX (không dùng pdfLaTeX, XeLaTeX hay Tectonic với lớp này), bộ phông Liberation và các gói trong `tex-env.nix`. Đặt thư mục `uet-graduation-latex/` cạnh `internship-report/`, cùng hình `results/figures/forest-scaling.pdf`, như cấu trúc dự án/gói nguồn.

```bash
bash internship-report/build_pdf.sh
```

Nếu không có LuaLaTeX nhưng có Nix, script sử dụng `tex-env.nix`; lần đầu có thể tải gói TeX. Bộ nhớ đệm LuaLaTeX đặt trong `internship-report/build/tex-cache/`, không yêu cầu ghi vào thư mục cấu hình cá nhân. Script biên dịch ba lượt để hoàn tất mục lục, trích dẫn và tham chiếu.

Hệ thống hiện tại không có Times New Roman. Bản PDF dùng **Liberation Serif**, phông tự do tương thích kích thước với Times; phông toán được cấu hình để không mất ký tự. Khi cài Times New Roman, lớp sẽ dùng phông đó. Khổ A4, lề và cỡ chữ thân bài 13 pt kế thừa `uetgraduation.cls`; trang bìa và trang nhận xét điều chỉnh theo `template.pdf` dành cho thực tập, không dùng hai trang bìa khóa luận mặc định.

## Cập nhật bảng khi có dữ liệu nghiên cứu mới

```bash
python3 internship-report/prepare_report.py
bash internship-report/build_pdf.sh
```

Script chỉ đọc kết quả hiện có và ghi bảng trong báo cáo. Nó kiểm tra SHA-256, số mẫu, số đếm và tính lại GM; không chạy thuật toán, không thay đổi CSV benchmark hoặc PDF khóa luận. Nếu bộ dữ liệu đổi, cần cập nhật bản kê nghiên cứu tương ứng trước khi tạo bảng. Không sửa số đo bằng tay trong `generated/`.

Sau khi dựng, có thể kiểm tra số trang, trích dẫn, lỗi ký tự và dữ liệu bằng `python3 internship-report/validate_report.py` (cần Poppler trong PATH). Tệp `generated/verification.json` ghi kết quả kiểm tra. Kiểm tra tự động không thay thế việc xem từng trang PDF.

`generated/visual-review.json` ghi SHA-256 của bản PDF đã được duyệt từng trang; nếu dựng ra PDF khác, kết quả kiểm tra sẽ báo cần duyệt hình thức lại.

## Phạm vi kết luận

So sánh rừng dùng bản tái hiện truy hồi bài gốc sau nén hạng; so sánh TTSP, partial 2-tree và cactus dùng đối chứng trong dự án. Báo cáo không đồng nhất chúng với phép đo mã của tác giả paper. XP theo treewidth không được viết thành FPT chỉ theo treewidth. Kết quả series–parallel là đề xuất có lập luận và kiểm chứng của đề tài, chưa phải xác nhận phản biện độc lập hoặc tuyên bố tính mới toàn cầu.

Mẫu yêu cầu **10–15 trang nội dung**. Trang bìa, mục lục, lời cảm ơn, tóm tắt, tài liệu tham khảo và nhận xét không tính vào phần nội dung. Hai nhãn `report:body:start` và `report:body:end` dùng để kiểm tra số trang sau mỗi lần dựng.
