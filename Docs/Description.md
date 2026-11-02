# ANIMEMMORPG — MÔ TẢ GAME

> Bản thiết kế mới lấy cảm hứng từ tinh thần chiến đấu, phối hợp và cạnh tranh của Vinh Diệu trong Toàn Chức Cao Thủ; nghề nghiệp, thế giới và luật chơi được thiết kế riêng. Các quyết định bên dưới thay thế định hướng cũ theo yêu cầu thiết kế lại. Thông số là thiết kế nền tảng, chưa phải kết quả cân bằng thực nghiệm. Engine Unreal Engine 5.8.4; khoảng cách dùng mét (m), thời gian dùng giây. Nội dung ghi “Chưa chốt” không được xem là tính năng đã được định nghĩa đầy đủ.

## 1. Tổng quan

AnimeMMORPG là MMORPG hành động 3D phong cách anime trên PC, trong thế giới fantasy pha cơ khí. Người chơi tự tạo nhân vật, chọn nghề, học kỹ năng, khám phá, chế tạo và tham gia dungeon, boss, bang hội hoặc đấu trường.

Combat đề cao khả năng tự ngắm, giữ khoảng cách, đọc động tác và phối hợp. PvE cung cấp tiến trình và tài nguyên; PvP chuẩn hóa sức mạnh để thử kỹ năng và chiến thuật. Game không dùng nhân vật anh hùng cố định, Linh Căn hoặc gacha trong phạm vi mô tả hiện tại.

## 2. Trải nghiệm game mang lại

Người chơi thăm dò, áp sát, tạo sơ hở, nối kỹ năng rồi truy kích hoặc rút lui. Combo là chuỗi quyết định theo tình huống, không chỉ bấm lặp một nút. Người bị ép vẫn có cách phòng thủ và thoát hiểm.

Tiến bộ đến từ hiểu nghề, thao tác, lựa chọn build, trang bị và phối hợp. Khám phá và chế tạo có giá trị riêng; không bắt buộc mọi người tham gia xếp hạng.

## 3. Nhân vật người chơi

Nhân vật có ngoại hình và tên do người chơi chọn; ngoại hình không tạo lợi thế chiến đấu. Mỗi nhân vật có một nghề đang hoạt động. Đổi nghề tại thành phố, ngoài chiến đấu: giữ cấp nhân vật, phân lại điểm kỹ năng, vô hiệu trang bị không hợp nghề. Không đổi nghề trong dungeon hoặc PvP.

Thuộc tính gồm HP, năng lượng, công, thủ, chí mạng và sát thương chí mạng. Trang bị không tăng tùy ý tốc độ di chuyển hoặc rút ngắn hoạt ảnh. Trạng thái gồm di chuyển, trên không, tấn công, dùng kỹ năng, phòng thủ, né, khống chế, tương tác và đánh bại.

Chỉ hành động ghi cho phép mới được kết hợp di chuyển. Trên không chỉ dùng kỹ năng cho phép trên không; không né hoặc đỡ phổ thông. Tương tác yêu cầu không thực hiện hành động chiến đấu, nhận sát thương sẽ ngắt. Bị đánh bại chặn hành động ngoài lựa chọn hồi sinh.

## 4. Hệ thống chiến đấu

### 4.1. Định hướng combat

Góc nhìn thứ ba với camera tự do. Tấn công dựa trên hướng ngắm, vùng đánh và va chạm, không bảo đảm trúng chỉ vì chọn mục tiêu. Cận chiến xoay theo ngắm trong startup, cố định hướng khi vào active. Đạn thường không tự truy đuổi. Vật cản rắn chặn đòn trừ kỹ năng xuyên được ghi rõ.

### 4.2. Điều khiển

| Phím                  | Chức năng                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| WASD / chuột          | Di chuyển / xoay camera và ngắm                                                             |
| Chuột trái           | Đánh thường hoặc bắn thường                                                            |
| Chuột phải           | Đỡ ở nghề cận chiến và Hộ Ước; ngắm với Cơ Xạ; định vị kỹ năng với Ấn Sư |
| Space                  | Nhảy                                                                                          |
| Shift                  | Né theo hướng di chuyển, không có hướng thì lùi                                      |
| Ctrl giữ              | Chạy nước rút                                                                              |
| V                      | Đổi vai camera, giữ nguyên góc nhìn                                                      |
| Escape                 | Mở menu, giải phóng chuột và tạm khóa điều khiển nhân vật                          |
| Q, E, R, F, 1, 2, 3, 4 | Tám ô kỹ năng                                                                              |
| X                      | Thoát hiểm                                                                                   |
| G / I / K / M          | Tương tác / kho đồ / kỹ năng / bản đồ                                                |
| Tab                    | Đánh dấu mục tiêu để xem thông tin                                                     |

Cho phép đổi phím, độ nhạy và bên camera. Chạy thường 5 m/s, nước rút 7 m/s; nước rút dừng khi tấn công, dùng kỹ năng hoặc phòng thủ. Giữ Shift không tự lặp né. Chỉ nhận nước rút khi có hướng di chuyển và không bị khóa hành động.

WASD di chuyển theo hướng ngang của camera; nhìn lên hoặc xuống không làm nhân vật bay. Đi chéo không nhanh hơn đi thẳng. Mỗi lần nhấn Space chỉ nhảy một lần, giữ phím không tự nhảy lại và không có nhảy đôi. Độ cao nhảy mục tiêu là 1,2 m; có thể nhảy trong 0,10 giây sau khi rời nền hoặc bấm sớm tối đa 0,10 giây trước khi tiếp đất. Khoảng hỗ trợ sau khi rời nền không áp dụng sau cú nhảy chủ động. Dốc quá 45° không thể đi bộ lên và làm nhân vật trượt xuống. Khi tương tác hoặc bị đánh bại, nhân vật không di chuyển hoặc nhảy nhưng vẫn rơi theo trọng lực. Sau khi khóa điều khiển, phải thả phím đang giữ trước khi dùng lại lệnh đó.

Nhân vật quay theo hướng di chuyển; hướng ngắm lấy từ tâm camera và tồn tại riêng với hướng thân. Khi đứng yên, xoay camera không xoay thân. Camera không tự quay về sau lưng khi chạy. Camera thu vào ngay trước vật cản và trở ra có làm mượt khi đường nhìn thông thoáng; khi quá gần, hình nhân vật tạm ẩn để tránh nhìn xuyên bên trong. Tương tác hoặc bị đánh bại vẫn cho phép xoay camera và mở menu.

Menu điều khiển cho phép đổi từng phím di chuyển, nhảy, nước rút, đổi vai và tương tác; chỉnh độ nhạy, đảo trục Y, chọn vai camera mặc định và khôi phục mặc định ngay. Kéo độ nhạy có hiệu lực ngay; thả thanh chỉnh, chọn Save hoặc Resume sẽ lưu thay đổi. Thiết lập được lưu cho lần chơi sau. Phím trùng bị từ chối và giải thích, không tự đổi chỗ; các phím dành cho combat và Escape không bị chiếm cho hành động khác. Escape trong lúc đổi phím sẽ hủy thay đổi đang chờ.

Mở menu hoặc chuyển sang cửa sổ khác sẽ thả chuột và xóa lệnh điều khiển đang đệm. Quay lại cửa sổ không tự bật điều khiển: cần chọn Resume. Menu chỉ khóa điều khiển, thế giới và trọng lực vẫn tiếp tục chạy.

### 4.3. Đòn đánh thường và combo

**Quyền hành động của bộ kiếm tham chiếu.** Đánh/kỹ năng dừng ngay vận tốc ngang, khóa di chuyển và nhảy nhưng tiếp tục trọng lực. Trong startup thân theo yaw ngắm mới nhất, từ active khóa hướng đến hết đòn; camera vẫn tự do. Đỡ theo yaw ngắm, bước 2 m/s theo camera, không nhảy/sprint. Ngoài combat thân quay theo hướng di chuyển. Recovery kết thúc cho phép đi tiếp với WASD đang giữ, không yêu cầu thả phím như khóa menu/Defeated. Trên không không đánh/né/đỡ hoặc dùng Q/E của bộ kiếm tham chiếu; X vẫn dùng khi bị khống chế cứng. Tương tác phải kết thúc trước combat. Đánh bại chặn hành động chiến đấu; hồi sinh theo mục 19, camera/menu vẫn dùng được. Mất nền khi đánh hủy phần chưa phát, reset combo, rơi và không hoàn tài nguyên. Menu/mất focus xóa lệnh chờ, bỏ đỡ; không hủy đòn đã nhận, recovery, cooldown, trọng lực hoặc đòn địch.

Mỗi nghề có bộ đánh thường riêng. Bộ kiếm tham chiếu gồm ba đòn sát thương thô 60/70/90; tổng thời lượng 0,40/0,45/0,60. Khoảng active lần lượt là [0,16;0,22), [0,18;0,25), [0,26;0,36). Phần trước active là startup; phần sau là recovery. Tổng chuỗi 220 sát thương trong 1,45 giây khi nối ngay.

Lệnh đánh tiếp được đệm tối đa 0,15 giây, thực hiện khi động tác hiện tại kết thúc. Sau đòn 1 hoặc 2 có thêm 0,15 giây để nối; quá hạn quay về đòn 1. Né, kỹ năng, khống chế và đánh bại reset chuỗi. Mỗi lần ra đòn chỉ trúng mỗi mục tiêu một lần; kỹ năng nhiều hit phải ghi rõ số hit và khoảng thời gian.

Đánh thường được hủy startup bằng né hoặc đỡ, không hủy active. Chỉ kỹ năng ghi quyền nối mới hủy recovery. Chiêu đã khởi động không hoàn hồi chiêu chỉ vì bị hủy. Không có đường hủy tạo combo vô hạn.

**Lệnh và vùng kiếm tham chiếu.** Chuột trái chỉ nhận cạnh nhấn, không Feint và không tự lặp khi giữ. Buffer một lệnh đánh, sống 0,15 giây; nhấn mới thay lệnh cũ. Hủy startup bằng đỡ cũng reset combo. Ba đòn dùng cùng hộp rộng 1,20 m, cao 1,80 m, sâu 2 m từ vị trí chân nhân vật về phía trước; tâm cao 0,90 m và cách nhân vật 1 m về phía trước. Hình dáng kiếm không tự thay vùng đánh. Lệnh cùng thời điểm ưu tiên X hợp lệ → né → bắt đầu đỡ → Feint → Q → E → đánh thường → nhảy; khác thời điểm giữ thứ tự tiếp nhận. Lệnh bị từ chối có lý do và không tiêu tài nguyên.

### 4.4. Theo dõi mục tiêu

Tab chọn đối thủ sống, nhìn thấy trong 20 m, gần tâm camera nhất; hòa thì ưu tiên gần nhân vật. Giữ đánh dấu tối đa 30 m; bị che liên tục 1 giây thì bỏ. Nhìn thấy lại reset bộ đếm. Khoảng cách tính theo vị trí 3D. Đánh dấu không xoay camera, tự hướng đòn hoặc chuyển sang mục tiêu khác khi đối thủ chết.

**Quy tắc giữ và bỏ đánh dấu.** Nhấn Tab khi đã đánh dấu sẽ bỏ chọn. Khoảng cách lấy giữa vị trí nhân vật; hòa cả khoảng cách thì mã chủ thể tăng dần. Chọn mới cần điểm ngắm trên màn hình và đường nhìn camera không bị môi trường chặn. Ra ngoài màn hình đơn thuần vẫn giữ đánh dấu nhưng ẩn marker/thông tin HP; che khuất môi trường liên tục mới tính thời hạn 1 giây. Mục tiêu chết hoặc bắt đầu lượt sống mới thì bỏ chọn ngay; không tự chuyển mục tiêu.

### 4.5. Né và phòng thủ

Né dịch chuyển 3 m trong 0,25 giây, vận tốc trung bình 12 m/s; khóa tấn công đến 0,35 giây. Tối thiểu 0,60 giây giữa hai lần bắt đầu né. Có hai lượt, hồi tuần tự một lượt mỗi 2 giây từ lúc tiêu lượt đầu; dùng tiếp không reset hồi. Né được chấp nhận vẫn tiêu lượt khi bị vật cản chặn. Không xuyên người, tường hoặc tự vượt vực.

Né không có bất tử chung, Perfect Dodge, Snapshot Ghost hoặc tự lựa động tác theo đối thủ. Thành công bằng việc rời vùng đánh. Kỹ năng nghề có miễn nhiễm phải mô tả riêng. Đệm né 0,15 giây chỉ trong trạng thái né hoặc chờ đủ 0,60 giây; không đệm khi hết lượt, chịu khống chế hoặc trong active/recovery của đòn đánh.

Đỡ che phía trước trong góc 120 độ, giảm 70% sát thương trực tiếp; không đỡ đòn bắt, đòn xuyên đỡ hoặc sát thương định kỳ đã có. Thế đỡ tối đa 100, mất 25 mỗi hit; về 0 gây phá đỡ 0,8 giây rồi hồi đầy. Ngoài đỡ và không nhận đòn 2 giây thì hồi 25 điểm/giây. Không đỡ khi né, trên không hoặc chịu khống chế.

**Parry — đỡ đúng lúc**

Kiếm Vũ, Phá Trận, Ảnh Quyền và Hộ Ước dùng parry qua nút đỡ. Một lần nhấn mới hợp lệ mở cửa sổ [0; 0,12) giây từ lúc bắt đầu đỡ. Phải nhả rồi nhấn lại, tối thiểu 0,60 giây giữa hai lần mở. Giữ nút không lặp parry; bấm trong thời gian chờ chỉ đỡ thường, không đệm parry. Mở cửa sổ dù không gạt được đòn vẫn bắt đầu thời gian chờ. Đúng mốc 0,12 giây trở đi áp dụng đỡ thường.

Điều kiện: nhân vật được phép đỡ, còn thế đỡ, tiếp xúc trong góc đỡ 120 độ và hit được phép parry. Đòn thường cận chiến có thể parry; kỹ năng phải ghi riêng. Đạn, vùng sát thương, sát thương định kỳ, đòn bắt và xuyên đỡ không được parry theo mặc định. Đòn không thể parry có tín hiệu riêng; một đòn không parry được vẫn có thể đỡ thường nếu không xuyên đỡ.

Thành công chặn toàn bộ sát thương trực tiếp và hiệu ứng bất lợi của đúng hit được gạt, không mất thế đỡ cho hit đó. Cửa sổ đóng ngay sau một hit; hit tiếp theo xét đỡ thường nếu còn giữ nút. Không cấp bất tử, tự phản đạn, tự đánh trả hoặc tự ngắt đối thủ. Với hit đồng thời, máy chủ dùng thứ tự sự kiện ổn định; chỉ hit hợp lệ đầu tiên nhận parry. Sai thời điểm nhưng còn giữ đỡ áp dụng đỡ thường; sai hướng hoặc xuyên đỡ áp dụng luật trúng bình thường.

Sau thành công, người chơi chủ động bỏ đỡ để đánh hoặc dùng kỹ năng đang sẵn sàng, vẫn chịu startup, chi phí và hồi chiêu bình thường. Không bảo đảm đòn trả trúng. Kỹ năng phản công riêng phải định nghĩa điều kiện, thời hạn và đánh đổi; không mặc định cộng cho mọi nghề. Kiếm Vũ thiên về phản công, Hộ Ước thiên về giữ tuyến và bảo vệ. Cơ Xạ và Ấn Sư không có parry phổ thông.

Máy chủ quyết định thời điểm bắt đầu đỡ, hướng và thứ tự hit. Khi thời điểm bằng nhau, thứ tự ổn định theo mã chủ thể rồi mã sự kiện; đánh bại có hiệu lực ngay, sự kiện tấn công sau đó từ chủ thể đã chết không hợp lệ. Dự đoán phía máy khách không xác nhận thành công; không tự nới cửa sổ theo ping. Chính sách bù trễ được chốt khi kiểm chứng mạng.

**Đòn giả, ngắt chiêu và phản công vị trí**

Feint chỉ áp dụng cho hành động có ghi cho phép. Trong startup, nhấn lại nút của chính hành động để hủy thành đòn giả; ưu tiên lệnh này trước nối combo. Hủy trước active nên không sinh hit; khóa tấn công, đỡ/parry, né và kỹ năng khác 0,20 giây, vẫn được di chuyển nếu không bị khống chế. Tối thiểu 1 giây giữa hai lần Feint thành công; không hoàn tài nguyên/hồi chiêu đã tiêu. Lệnh không hợp lệ không hủy, vẫn theo bộ đệm gốc. Không mặc định mọi đòn thường đều có Feint; danh sách thuộc thiết kế nghề.

Interrupt chỉ xảy ra khi hit có thuộc tính ngắt trúng trong pha mục tiêu cho phép bị ngắt. Hit thường không tự ngắt mọi chiêu. Ngắt dừng các pha còn lại và hit chưa phát, không hoàn chi phí/hồi chiêu; không tự thêm choáng nếu không ghi hiệu ứng đó. Hiệu ứng đã phát theo luật riêng, trừ quy tắc đánh bại tại mục 19. Boss chỉ bị ngắt theo cửa sổ/thanh thế được báo hiệu, không tự bị parry ngắt mọi chiêu.

Đòn bắt khắc chế đỡ/parry nhưng có startup và vùng bắt rõ, có thể tránh bằng vị trí. Bắt mục tiêu trên không hoặc trong động tác đặc biệt phải ghi riêng. Phản công sau đối thủ đánh hụt là tận dụng recovery bằng đòn hợp lệ, không tự thêm sát thương thưởng. Các cơ chế này không cho phép hủy vô hạn hoặc vượt khóa hành động.

**Chi tiết phòng thủ và khống chế.** Các mốc 0,12 giây parry và 0,60 giây cooldown dùng khoảng nửa mở; cửa sổ đóng sau hit thành công đầu tiên theo thứ tự ổn định. Hit giảm thế đỡ từ 25 về 0 vẫn giảm 70% sát thương trước phá đỡ. Phá đỡ chịu luật chống khóa liên tục và dùng được X; khi thoát hồi đầy thế đỡ. Trong miễn khống chế cứng vẫn có thể vỡ thế đỡ/buộc bỏ đỡ rồi hồi đầy, nhưng không khóa 0,8 giây. Đỡ thành công chặn hiệu ứng gắn hit của bộ kiếm tham chiếu trừ xuyên đỡ/bắt. Né khóa cả bắt đầu nhảy/đỡ/tương tác đến 0,35 giây; hướng khóa lúc nhận, va chạm và nền giới hạn quãng đường dịch chuyển; mất nền ngoài ý muốn thì kết thúc dịch chuyển và rơi. Không hoàn lượt khi bị chặn. Slow dùng mức mạnh nhất, không cộng. Choáng, quật ngã, hất tung và bắt dùng cùng luật thay thế thời gian còn lại và chống khóa. Bộ kiếm tham chiếu chưa có kỹ năng bắt hoặc combo trên không.

### 4.6. Kỹ năng và khống chế

**Hai kỹ năng mẫu của Kiếm Vũ** (thông số nền thử nghiệm, tên làm việc; chưa phải tám kỹ năng nghề):

| Thuộc tính                | Q — Hư Trảm                  | E — Phá Thế                               |
| --------------------------- | ------------------------------- | -------------------------------------------- |
| Sát thương thô          | 100                             | 80                                           |
| Startup                     | 0,30 giây                      | 0,25 giây                                   |
| Active                      | [0,30; 0,40)                    | [0,25; 0,35)                                 |
| Tổng thời lượng         | 0,80 giây                      | 0,75 giây                                   |
| Năng lượng / hồi chiêu | 20 / 4 giây                    | 25 / 6 giây                                 |
| Vùng đánh                | Hộp kiếm tại 4.3             | Hộp kiếm tại 4.3                          |
| Phòng thủ                 | Đỡ và parry được          | Đỡ và parry được                       |
| Feint                       | Nhấn Q lần nữa trong startup | Không                                       |
| Gây Interrupt              | Không                          | Có khi hit trực tiếp trúng pha cho phép |
| Bị Interrupt               | Chỉ startup                    | Chỉ startup                                 |

Q/E hủy được recovery đánh thường, không hủy startup/active đánh thường hoặc hủy lẫn nhau. Startup Q/E được né/đỡ hủy; active/recovery không được né/đỡ hủy. Q/E không có bộ đệm lệnh. Chi phí/cooldown bắt đầu lúc chấp nhận, kể cả bị ngắt/Feint; Feint Q khóa đánh/đỡ/né/kỹ năng/nhảy 0,20 giây, cho đi thường nhưng không sprint, cách Feint trước ít nhất 1 giây. E không tự stun; block/parry chặn Interrupt, chỉ hit trực tiếp hợp lệ mới ngắt. Đánh thường cũng cho bị Interrupt trong startup; active/recovery không bị Interrupt thuần túy. Khống chế cứng/đánh bại có quyền riêng.

Trang bị tám kỹ năng nghề ngoài đánh thường, phòng thủ và thoát hiểm. Thay bộ kỹ năng tại thành phố hoặc điểm chuẩn bị dungeon, ngoài chiến đấu. Mỗi kỹ năng phải xác định startup, active, recovery, chi phí, hồi chiêu, tầm, điều kiện trúng, khả năng di chuyển và quyền hủy. Chi phí/hồi chiêu tính khi lệnh được chấp nhận; bị ngắt không hoàn lại, lệnh bị từ chối không tiêu tài nguyên.

Khống chế mềm làm chậm nhưng không khóa hành động. Khống chế cứng gồm choáng, hất tung, quật ngã và bắt. Thời lượng không cộng dồn; hiệu ứng mới chỉ thay hiệu ứng hiện tại khi thời gian còn lại dài hơn. Một người chơi bị khóa liên tục tối đa 2 giây; chạm giới hạn thì thoát và miễn khống chế cứng 2 giây, không miễn sát thương. Chỉ reset thời gian khống chế tích lũy sau khi nhân vật có 0,50 giây liên tục không chịu khống chế cứng; thời gian tự do không cộng vào thời gian bị khóa. Thoát hiểm giải hiệu ứng, xóa bộ đếm tích lũy và cấp miễn khống chế theo luật riêng.

Thoát hiểm X hồi 30 giây, dùng được khi đang chịu khống chế cứng, giải hiệu ứng và miễn khống chế cứng 1 giây. Không gây sát thương hoặc miễn sát thương. Boss không chịu bắt/hất tung; kỹ năng ngắt ảnh hưởng thanh thế theo quy tắc riêng của boss.

Năng lượng nền tối đa 100, hồi 10 mỗi giây sau 1 giây không tiêu năng lượng. Đánh thường, né, đỡ và thoát hiểm không tiêu năng lượng; kỹ năng có chi phí riêng, không đủ thì từ chối và không bắt đầu hồi chiêu. Bắt bỏ qua đỡ/parry nhưng bị miễn khống chế cứng chặn; phần sát thương vẫn xét riêng.

### 4.7. Sát thương và HP

Sát thương cuối = sát thương thô kỹ năng × hệ số công × 100/(100 + thủ), sau đó áp dụng chí mạng và giảm sát thương từ đỡ. Thủ không âm; làm tròn kết quả cuối tới số nguyên gần nhất. Chí mạng nền 5%, gây 150% sát thương. Khiên hấp thụ trước HP; HP không dưới 0.

Mốc cấp đầu: người chơi 1.000 HP, quái thường 600 HP, hệ số công 1, thủ 0. Ba combo kiếm gây 660, hạ quái ở hit thứ 9; quái gây 100 mỗi hit, hạ người chơi sau 10 hit. Ví dụ không tính chí mạng, đỡ, khiên hoặc hồi máu, không đại diện mọi cấp/nghề.

Sát thương đúng nửa được làm tròn lên sau toàn bộ hệ số. Khiên hấp thụ trước HP, không chặn hiệu ứng nếu hit không được phòng thủ chặn; sát thương dương được khiên hấp thụ vẫn ngắt tương tác. Bộ kiếm tham chiếu chưa có kỹ năng tạo khiên.

## 5. Nghề nghiệp và vũ khí

| Nghề       | Bản sắc                                                    | Điểm yếu                                         |
| ----------- | ------------------------------------------------------------ | --------------------------------------------------- |
| Kiếm Vũ   | Kiếm đơn; phản công, đổi góc, nối đòn chính xác | Tầm ngắn, hụt đòn dễ bị phản công          |
| Phá Trận  | Trường thương; giữ cự ly, đẩy kéo, chia đội hình | Khó xoay trở khi bị áp sát nhiều hướng      |
| Ảnh Quyền | Găng tay; quyền cước, áp lực gần, bắt quật          | Khó tiếp cận đối thủ giữ khoảng cách       |
| Cơ Xạ     | Súng cơ khí; ngắm, quản lý đạn, đặt bẫy           | Dễ bị ép khi nạp đạn, cần đường bắn      |
| Ấn Sư     | Pháp khí; đặt ấn, kích hoạt vùng ảnh hưởng        | Cần chuẩn bị, dễ mất nhịp khi bị ngắt       |
| Hộ Ước   | Khiên và pháp ấn; bảo vệ, cứu nguy, giữ tuyến       | Sát thương cá nhân thấp, cần đúng vị trí |

Mỗi nhân vật khởi đầu bằng vũ khí tập luyện đúng nghề. Một bộ vũ khí nghề hoạt động trong giao tranh; chỉ đổi trang bị ngoài chiến đấu. Không có hai ô vũ khí để bỏ recovery, Tán Nhân hoặc vũ khí mở kỹ năng mọi nghề.

Biến Thức là hướng thay đổi cách dùng kỹ năng với đánh đổi: Kiếm Vũ phản công/truy kích; Phá Trận giữ tuyến/phá tuyến; Ảnh Quyền áp lực/bắt quật; Cơ Xạ cơ động/bẫy; Ấn Sư bộc phát/kiểm soát; Hộ Ước bảo vệ/hỗ trợ. Chọn một hướng khi chuẩn bị build. Danh sách kỹ năng và đánh đổi cụ thể từng hướng chưa chốt.

## 6. Thuộc tính sát thương và hiệu ứng

Không có Linh Căn, Song Tu hoặc thức tỉnh theo chỉ số. Nguyên tố là đặc tính kỹ năng và ngôn ngữ hình ảnh; không có bảng phản ứng toàn cục. Cháy, làm chậm, điện giật chỉ tồn tại khi kỹ năng ghi rõ, không tự suy ra từ màu hiệu ứng.

Khiên có dung lượng và thời hạn; cùng nguồn thay khiên cũ, khác nguồn cộng dung lượng. Khiên không miễn khống chế. Hồi máu không vượt HP tối đa. Vùng kỹ năng phải có ranh giới, thời lượng và đối tượng tác dụng rõ.

Với bộ quy tắc tham chiếu, khiên cùng nguồn thay cả dung lượng và thời hạn. Khi nhiều nguồn còn hiệu lực, hấp thụ nguồn hết hạn sớm trước, hòa thì source ID tăng dần; đúng deadline đã hết hiệu lực. Quy tắc này không tự cấp kỹ năng tạo khiên cho Kiếm Vũ.

## 7. Kẻ địch và AI chiến đấu

Quái thường dạy đọc đòn; tinh anh phối hợp; boss kiểm tra cơ chế và tổ đội. Đòn nguy hiểm có tín hiệu nhìn/nghe được. Quái tham chiếu: startup 0,60, active 0,15, recovery 0,75 giây; chu kỳ 1,50 giây, tầm cận chiến 2 m. Trong active chỉ gây sát thương khi vùng đánh chạm mục tiêu.

Quái truy đuổi trong khu vực của mình. Về điểm xuất phát thì hồi HP, kết thúc quyền nhận thưởng giao tranh cũ. Boss không bị kéo ra ngoài khu chiến đấu. Mỗi boss có thanh thế và thời điểm có thể ngắt riêng, hiển thị rõ cho người chơi.

**Quái cận chiến tham chiếu.** 600 HP, 100 damage; startup 0,60, active 0,15, recovery 0,75 giây, tầm 2 m. Theo mục tiêu trong startup, khóa hướng từ active, chỉ startup bị Interrupt. Truy đuổi 3 m/s, phát hiện 10 m có đường nhìn, leash 15 m từ spawn. Mất mục tiêu/vượt leash thì về spawn; vào trong 0,5 m hồi đầy HP/reset. 

**Hành vi quái cận chiến tham chiếu.** Mất mục tiêu gồm mục tiêu chết, ra ngoài 10 m hoặc đường nhìn ở độ cao 0,90 m từ vị trí chân bị môi trường che. Bắt đầu về spawn hủy đòn đang chờ, không gây damage sau đó; không tái truy đuổi trước khi hoàn thành về spawn.  Quái dừng di chuyển ngang khi đánh; tư thế và vùng cảnh báo phân biệt startup/active/recovery.

## 8. Thế giới và khám phá

Thế giới gồm thành phố an toàn, vùng hoang dã, di tích cơ khí, dungeon và khu boss. Địa danh, lịch sử và phe phái chưa chốt. Không có PvP tự do; đấu tay đôi ngoài đấu trường cần hai bên đồng ý và không mất tài sản.

Khám phá cung cấp vật liệu, nhiệm vụ và lối tắt. Dịch chuyển giữa điểm đã mở chỉ ngoài chiến đấu. Nhảy dùng vượt địa hình thấp; leo tự do và thú cưỡi không thuộc thiết kế hiện tại.

## 9. Nhiệm vụ và hoạt động

Nhiệm vụ chính giới thiệu thế giới/nghề; nhiệm vụ phụ phục vụ khám phá và chế tạo. Hoạt động tuần cho nhiều mục tiêu lựa chọn, không bắt buộc đăng nhập hằng ngày.

Tiến trình riêng từng nhân vật. Mục tiêu hạ địch chia sẻ cho thành viên tổ đội có cùng nhiệm vụ, đang ở cùng instance và trong 30 m tính từ mục tiêu tại thời điểm bị hạ. Đồ nhiệm vụ cá nhân không bị người khác nhặt mất. Mỗi lần hoàn thành hợp lệ chỉ nhận thưởng một lần. Cốt truyện và danh sách nhiệm vụ chưa chốt.

## 10. Tiến trình phát triển nhân vật

Cấp tối đa 50. Kinh nghiệm đến từ nhiệm vụ, quái, dungeon và hoạt động PvP hợp lệ; đấu tay đôi tự tổ chức không cho kinh nghiệm. Mỗi cấp từ 2 đến 50 cho một điểm kỹ năng, tổng 49 điểm. Mở kỹ năng theo cấp/nhiệm vụ nghề; điểm nâng không đủ tối đa mọi lựa chọn. Phân lại miễn phí tại thành phố.

Build kết hợp nghề, tám kỹ năng, Biến Thức và trang bị. Đường cong kinh nghiệm, danh sách kỹ năng và chi phí từng cấp kỹ năng chưa chốt.

## 11. Trang bị, vật phẩm và kho đồ

Ô trang bị: bộ vũ khí nghề, đầu, thân, tay, chân, giày và hai phụ kiện. Sáu phẩm chất: Thường, Tốt, Hiếm, Sử Thi, Huyền Thoại, Kiệt Tác. Phẩm chất phản ánh ngân sách thuộc tính và độ đặc biệt, không bảo đảm phù hợp mọi build.

Bộ trang bị tính đầu, thân, tay, chân, giày và tối đa một phụ kiện; mốc 2/4/6 cộng dồn, mỗi mốc kích hoạt một lần. Món thuộc bộ nào được ghi rõ. Hai phụ kiện cùng bộ không tính thành hai món.

Mỗi món có tối đa một lỗ ngọc, ghi trên món. Ngọc có năm cấp; ba viên cùng loại/cấp ghép thành một viên cấp kế tiếp, không thất bại; cấp 5 không ghép lên nữa. Tháo không phá ngọc.

Kho nhân vật 80 ô, kho thành phố 160 ô. Nguyên liệu cùng loại xếp tối đa 999/ô, trang bị chiếm riêng. Đồ nhiệm vụ không chiếm ô thường. Khi đầy, thưởng chuyển vào kho nhận thưởng không hết hạn, không tự xóa.

## 12. Tài nguyên, nâng cấp và chế tạo

Vật liệu đến từ khám phá, quái, boss và tháo trang bị. Chế tạo chọn định hướng thuộc tính trong ngân sách của món; không cộng vô hạn hoặc mở kỹ năng nghề khác. Vũ khí tự chế thể hiện build qua lựa chọn hiệu ứng trong danh sách hợp lệ, không cho người chơi tự tạo luật mới.

Nâng trang bị tối đa +10, đủ tiền/nguyên liệu thì thành công, không phá đồ. Công thức, chi phí và mức tăng từng bậc chưa chốt. Tên/ngoại hình không tác động sức mạnh.

## 13. Boss, dungeon và nội dung tổ đội

Dungeon bốn người; bản cốt truyện một người có phần thưởng thấp hơn. Raid tám người yêu cầu phối hợp. Boss thế giới thưởng cá nhân; mở quyền thưởng khi trực tiếp gây sát thương, hồi phục hoặc bảo vệ người đang giao tranh trong cùng khu vực. Không chia toàn bộ thưởng theo tỷ lệ sát thương. Ngưỡng chống tham gia tượng trưng chưa chốt.

Đấu trường 1v1 và 3v3 có xếp hạng riêng. Trận tối đa 5 phút; thắng khi hạ toàn bộ đối thủ, không hồi sinh giữa trận. Hết giờ xét tổng HP còn lại/tổng HP tối đa của đội ban đầu; bằng nhau thì hòa. Mất kết nối giữ nhân vật trong trận, cho phép vào lại, không tạo bất tử.

PvP dùng cấp 50, cùng ngân sách điểm và danh sách trang bị chuẩn; mở toàn bộ kỹ năng nghề để chọn build đấu trường. Đồ PvE, nâng cấp và ngọc không tăng sức mạnh đấu trường. Người chơi chọn cấu hình từ cùng danh sách chuẩn, giữ ngoại hình. Không dùng đồ hồi phục từ kho và không mất trang bị khi thua.

## 14. Multiplayer, máy chủ và chống gian lận

Máy chủ quyết định vị trí hợp lệ, hit, sát thương, khống chế, hồi chiêu, tài nguyên và tài sản. Máy khách phản hồi động tác sớm nhưng phải sửa theo kết quả xác nhận. Combat dùng thời gian máy chủ; chính sách bù trễ chi tiết chưa chốt. Không coi hình ảnh né trên máy khách là bằng chứng chắc chắn tránh đòn.

Mỗi nhân vật có một phiên hoạt động. Thưởng, nhận đồ và giao dịch chỉ hoàn tất một lần; kết nối lại khôi phục kết quả xác nhận, không nhân bản tài sản. Ngoài chiến đấu nghĩa là không gây/nhận sát thương hoặc dùng kỹ năng thù địch trong 10 giây và không còn ở giao tranh boss/PvP đang diễn ra.

## 15. Giao diện người dùng

HUD gồm HP, năng lượng, thế đỡ khi có, lượt né, thoát hiểm, tám kỹ năng, khống chế, tâm ngắm và tổ đội. Cơ Xạ có đạn/nạp đạn. Đánh dấu không cho nhìn xuyên vật cản.

Menu gồm nhân vật, nghề, kỹ năng, Biến Thức, trang bị, kho, chế tạo và bản đồ. Kỹ năng hiển thị chi phí, hồi chiêu, tầm và quy tắc đặc biệt. Không dùng màu làm tín hiệu duy nhất của vùng nguy hiểm.

**Điều khiển và phản hồi chiến đấu.** Đánh, đỡ, né, thoát hiểm, Q/E và đánh dấu mục tiêu cho phép đổi phím đơn hoặc nút chuột, không wheel/tổ hợp. Xoay camera và Escape cố định. Phím trùng bị từ chối; R/F/1–4 dành kỹ năng, I/K/M dành menu. Khi nạp thiết lập cũ, giữ lựa chọn hợp lệ, chỉ trả phím xung đột về mặc định và báo rõ, không tự lưu khi nạp. Giữ nút qua menu/mất focus không tạo hành động khi Resume. Startup/active/recovery phân biệt bằng tư thế và tín hiệu ngoài màu; hit/block/parry/hụt/phá đỡ/Interrupt/Feint có phản hồi riêng.

**Phản hồi giao tranh.** HUD hiển thị tên phím đang dùng và tài nguyên thực tế. HP đối thủ vừa trúng chỉ hiện khi thấy được, không tự đánh dấu hoặc hướng đòn. Báo hụt khi đòn hoàn tất và không có hit hợp lệ. Thông báo quan trọng mặc định hiện 1,2 giây. Màu đi kèm chữ, hình và tư thế; parry có vòng tròn và âm hai nốt, block có vạch chắn, Feint/Interrupt có nhãn và âm riêng.

## 16. Đồ họa, hoạt ảnh và âm thanh

Phong cách anime với hình khối rõ, nghề nhận biết qua vũ khí và tư thế. Hiệu ứng khớp vùng đánh, không che startup. Hoạt ảnh thể hiện hụt đòn, đỡ, phá đỡ và thoát khống chế.

Có tùy chọn giảm hiệu ứng đồng đội nhưng giữ tín hiệu boss. Skin không thay vùng đánh, thời lượng hoặc độ dễ nhận biết. Âm thanh phân biệt đòn nguy hiểm, phản hồi trúng và thông báo quan trọng.

## 17. Kinh tế và mô hình doanh thu

Tiền game dùng mua bán NPC, chế tạo và nâng cấp. Giao dịch cần hai bên xác nhận nội dung cuối; thay đồ/tiền hủy xác nhận trước. Đồ nhiệm vụ và thưởng xếp hạng cá nhân không giao dịch. Trang bị gắn nhân vật khi trang bị lần đầu.

Nguồn tiêu hao là chế tạo, nâng cấp và vật phẩm PvE; không mất đồ ngẫu nhiên do nâng cấp/chết. Mô hình phát hành, cửa hàng và doanh thu chưa chốt. Tạm bỏ gacha khỏi mô tả. Nguyên tắc: không bán sức mạnh hoặc lợi thế thi đấu.

## 18. Xã hội và cộng đồng

Có chat khu vực/tổ đội/bang hội, bạn bè, mời tổ đội và tìm nhóm theo hoạt động. Bang hội tổ chức dungeon, raid, luyện đấu; không cộng chỉ số bắt buộc người chơi phải vào bang mạnh. Có chặn/báo cáo và giới hạn lời mời.

Không có chiến tranh lãnh thổ hoặc PvP cưỡng bức. Sự kiện cộng đồng tập trung PvE chung và giải đấu tự nguyện.

## 19. Chết, hồi sinh và thất bại

HP về 0 kích hoạt đánh bại một lần. Đòn mới dừng; đạn, vùng sát thương và sát thương định kỳ của chủ thể bị đánh bại ngừng gây sát thương. Áp dụng cho người chơi và quái.

Ngoài dungeon, hồi sinh tại điểm an toàn đã mở gần nhất sau 5 giây, đầy HP, không mất kinh nghiệm/đồ. Trong dungeon, đồng đội cứu bằng tương tác 5 giây; nhận sát thương hoặc làm hành động khác sẽ ngắt. Người được cứu có 30% HP. Không cứu trong giao tranh boss. Đội chết hết trở về checkpoint, boss reset; không mất thưởng đã nhận hợp lệ. Đấu trường theo mục 13.

## 20. Hiệu năng và độ ổn định

Mục tiêu 60 FPS tại 1080p trên cấu hình PC mục tiêu; cấu hình cụ thể chưa chốt. Mỗi phân khu thế giới tối đa 40 người, ưu tiên giữ tổ đội cùng nhau. Dungeon/raid theo mục 13.

Giao tranh đông người vẫn đọc được hướng đòn và vùng nguy hiểm. Giảm chất lượng hình ảnh không giấu thông tin gameplay. Tiến trình/giao dịch đã xác nhận không mất vì ngắt kết nối.

## 21. Nguyên tắc thiết kế

Một đòn có thể trúng nhiều đối thủ; cơ thể đối thủ không tự chặn vũ khí như tường. X giải khống chế cứng và slow đang có, xóa tích lũy và xung hất tung chưa áp dụng; không miễn sát thương. Slow chỉ giảm tốc di chuyển chủ động, không đổi tốc độ hoặc quãng đường né.

Thao tác và quyết định có ý nghĩa; mọi nghề có điểm mạnh/cách khắc chế. Không combo khóa vô hạn. PvE thưởng tiến trình, PvP xếp hạng không cho lợi thế sức mạnh nhờ cày lâu. Không bắt buộc trả tiền để cạnh tranh. Hình ảnh, âm thanh, luật và giao diện phải thống nhất.

## 22. Các điểm chưa quyết định

| Chủ đề     | Nội dung còn mở                                                                 |
| ------------- | ---------------------------------------------------------------------------------- |
| Thế giới    | Địa danh, lịch sử, phe phái, cốt truyện                                     |
| Nghề         | Danh sách kỹ năng, chi phí, hồi chiêu, Biến Thức; đạn/nạp đạn Cơ Xạ |
| Cân bằng    | Đường cong chỉ số/kinh nghiệm; thông số quái, boss và trang bị          |
| Chế tạo     | Công thức, chi phí +1 đến +10, thuộc tính/hiệu ứng hợp lệ               |
| Nội dung     | Nhiệm vụ, dungeon, raid, boss và bảng thưởng; ngưỡng đóng góp boss      |
| PvP           | Ghép trận, xếp hạng, cấu hình trang bị chuẩn                               |
| Multiplayer   | Chính sách bù trễ, vùng máy chủ, tải toàn hệ thống                      |
| Hiệu năng   | Cấu hình PC tối thiểu và mục tiêu                                           |
| Thương mại | Mô hình phát hành/doanh thu; chưa thiết kế gacha                            |

Các nội dung còn mở không được tự suy diễn thành hệ thống đã hoàn chỉnh. Bản mô tả xác định nền tảng game, không thay thế danh mục từng kỹ năng, vật phẩm và nhiệm vụ.

## 23. Kết luận

AnimeMMORPG kết hợp thế giới online lâu dài với combat tự ngắm, nghề nghiệp có bản sắc, combo kỹ năng và phối hợp chiến thuật. Người chơi tạo dấu ấn qua điều khiển, build và chế tạo; chinh phục PvE và thi đấu công bằng mà không cần nhân vật hoặc vũ khí làm được mọi thứ.
