1. Thông tin cá nhân
Thông tin cá nhân của bạn <tên> api: https://api-uat.kingwork.vn/api/employee/search-employee
2. Phụ thuộc (Dependent)
Bạn <tên> có người phụ thuộc hay không? api: https://api-uat.kingwork.vn/api/employee/search-employee (relative)
Người phụ thuộc của bạn <tên> là ai?  api: https://api-uat.kingwork.vn/api/employee/search-employee (relative)
3. Hợp đồng (Contract)
Thời hạn bắt đầu hợp đồng của bạn <tên> khi nào?  api: api: https://api-uat.kingwork.vn/api/employee/search-employee (contract*)
Thời hạn hết hạn hợp đồng của bạn <tên> khi nào? api: https://api-uat.kingwork.vn/api/employee/search-employee (contract*)
Trạng thái, loại hợp đồng hiện tại của bạn là gì? api: https://api-uat.kingwork.vn/api/employee/search-employee (contract*)
4. Phép năm & Ngày nghỉ/OT (Leave & Overtime)
api lấy loại phép: https://api-uat.kingwork.vn/api/configurations/get-active-config-leave-off
api lấy thông tin phép của từng người: https://api-uat.kingwork.vn/api/timesheet/leave-type-off-employee-detail/7feb5d15-ec8c-4057-a61b-a429fe9247a6?
api lấy bảng timesheet của từng người: https://api-uat.kingwork.vn/api/timesheet/working-month/employee-timesheet-month?monthYear=2025-04&userId=1081e472-dd25-4871-af0a-80c886698781
 
Bạn <tên> còn bao nhiêu ngày phép năm? api: https://api-uat.kingwork.vn/api/timesheet/list-mamager-leave-off-employee?status=true&leaveTypeId=8&fromDate=2025-06-01&toDate=2025-06-30&configTypeId=3
Bạn <tên> đang có những loại ngày phép gì?
Tổng số giờ nghỉ phép trong tháng của bạn <tên>.
Bạn <tên> trong tháng có leave off hay OT ngày nào không? (nếu có thì nêu rõ ngày)
5. Lương & Phụ cấp (Compensation)
api này cần có OTP để lấy. này chưa có.
Thực nhận của bạn <tên> trong tháng <số> là bao nhiêu? api: 
Bạn <tên> có mức lương bao nhiêu?
Bạn <tên> có phụ cấp gì không? api: https://api-uat.kingwork.vn/api/timesheet/working-month/employee-timesheet-month?monthYear=2025-04&userId=1081e472-dd25-4871-af0a-80c886698781
6. Dự án (Project Assignment)
tổng dự án: https://api-uat.kingwork.vn/api/project
thông tin chi tiết của dự án <projectCode> : https://api-uat.kingwork.vn/api/project-detail/history/search?projectCode=
 
Bạn <tên> đang nằm trong dự án nào? 
Có những dự án nào ?
Thời hạn của dự án <tên>, ngày start, ngày kết thúc.
7. Timesheet & Giờ làm việc (Timesheet & Working Hours)
Tổng số giờ/ngày làm của bạn <tên> là bao nhiêu?
Còn bao nhiêu bạn trong tháng này chưa confirm timesheet?
Danh sách những bạn chấm không full công trong tháng (các cột: tên, MSNV, lý do).
8. Đánh giá hiệu suất (Performance Reviews)

get data những người được add performance: https://api-uat.kingwork.vn/api/performance/manager-view/underline-employees?limit=10&page=1&searchText=
chi tiết từng người: https://api-uat.kingwork.vn/api/performance/review/assessment?userId=201b6737-b68a-4be2-abf4-1753679099c9
 
Từ khi onboard thì bạn có mấy đợt đánh giá performant?
Thông tin chi tiết trong note về đánh giá bạn.