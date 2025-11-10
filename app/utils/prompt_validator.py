from __future__ import annotations

import re
from typing import List, Tuple


class PromptValidator:
    """Validator for image generation prompts to ensure educational and appropriate content."""
    
    # Từ khóa cấm - nội dung không phù hợp
    BANNED_KEYWORDS = [
        # Nội dung không phù hợp
        'nude', 'naked', 'sex', 'sexual', 'porn', 'explicit', 'nsfw',
        'violence', 'blood', 'gore', 'kill', 'murder', 'war crime',
        'drug', 'alcohol', 'smoke', 'cigarette',
        # Từ khóa tiếng Việt không phù hợp
        'khỏa thân', 'khiêu dâm', 'bạo lực', 'máu me', 'giết người',
        'ma túy', 'rượu bia', 'thuốc lá',
        # Nội dung chính trị nhạy cảm
        'propaganda', 'political', 'rebellion', 'revolution',
        'nổi dậy', 'phản động', 'chính trị',
    ]
    
    # Từ khóa yêu cầu - phải liên quan đến lịch sử VN
    REQUIRED_KEYWORDS = [
        # Lịch sử VN
        'việt nam', 'vietnam', 'việt', 'viet',
        'lịch sử', 'history', 'historical',
        # Triều đại
        'nhà trần', 'nhà lý', 'nhà nguyễn', 'nhà lê', 'nhà hồ',
        'triều đại', 'dynasty',
        # Nhân vật lịch sử
        'vua', 'hoàng đế', 'emperor', 'king',
        'quang trung', 'lý thái tổ', 'trần hưng đạo',
        'lý thường kiệt', 'nguyễn huệ', 'lê lợi',
        # Sự kiện lịch sử
        'trận', 'battle', 'chiến tranh', 'war',
        'bạch đằng', 'đống đa', 'ngọc hồi',
        'chiến thắng', 'victory',
        # Văn hóa
        'áo dài', 'trang phục', 'costume', 'traditional',
        'truyền thống', 'văn hóa', 'culture',
    ]
    
    # Từ khóa cảnh báo - cần kiểm tra kỹ
    WARNING_KEYWORDS = [
        'modern', 'hiện đại', 'contemporary',
        'future', 'tương lai', 'sci-fi', 'fantasy',
        'anime', 'manga', 'cartoon', 'hoạt hình',
    ]
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> Tuple[bool, str]:
        """
        Validate image generation prompt.
        Returns (is_valid, error_message)
        """
        prompt_lower = prompt.lower()
        
        # Kiểm tra từ khóa cấm
        for keyword in cls.BANNED_KEYWORDS:
            if keyword in prompt_lower:
                return False, f"Prompt chứa nội dung không phù hợp. Vui lòng chỉ tạo ảnh về lịch sử Việt Nam."
        
        # Kiểm tra có liên quan đến lịch sử VN không
        has_vietnam_history = any(keyword in prompt_lower for keyword in cls.REQUIRED_KEYWORDS)
        
        if not has_vietnam_history:
            return False, (
                "Prompt phải liên quan đến lịch sử Việt Nam. "
                "Vui lòng mô tả về nhân vật, sự kiện, hoặc triều đại trong lịch sử Việt Nam."
            )
        
        # Kiểm tra độ dài
        if len(prompt.strip()) < 10:
            return False, "Prompt quá ngắn. Vui lòng mô tả chi tiết hơn."
        
        if len(prompt.strip()) > 500:
            return False, "Prompt quá dài. Vui lòng rút gọn xuống dưới 500 ký tự."
        
        # Kiểm tra cảnh báo
        has_warning = any(keyword in prompt_lower for keyword in cls.WARNING_KEYWORDS)
        if has_warning:
            # Vẫn cho phép nhưng sẽ thêm instruction để đảm bảo về lịch sử VN
            pass
        
        return True, ""
    
    @classmethod
    def enhance_prompt(cls, prompt: str) -> str:
        """
        Enhance prompt with safety and educational instructions.
        """
        enhanced = (
            f"{prompt}. "
            "Phong cách truyện tranh comics giáo dục, chủ đề lịch sử Việt Nam chính xác, "
            "trang phục truyền thống Việt Nam, màu sắc sống động phù hợp, "
            "chi tiết rõ ràng, phong cách nghệ thuật châu Á, "
            "nội dung giáo dục và phù hợp với học sinh, "
            "không có nội dung bạo lực hoặc không phù hợp, "
            "tập trung vào giá trị lịch sử và văn hóa Việt Nam."
        )
        return enhanced
    
    @classmethod
    def add_safety_instruction(cls) -> str:
        """
        Get system instruction for safe image generation.
        """
        return (
            "Bạn là AI tạo ảnh giáo dục về lịch sử Việt Nam. "
            "Chỉ tạo ảnh về các sự kiện, nhân vật, và văn hóa lịch sử Việt Nam chính xác. "
            "Không tạo ảnh có nội dung bạo lực, không phù hợp, hoặc sai lệch lịch sử. "
            "Tập trung vào giá trị giáo dục và văn hóa truyền thống Việt Nam. "
            "Phong cách truyện tranh comics phù hợp với học sinh."
        )

