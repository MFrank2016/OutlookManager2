#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码检测器模块

功能：
- 从邮件主题和正文中提取验证码
- 支持多种验证码格式（数字、字母数字组合）
- 支持多语言关键词识别
"""

import re
from typing import Optional, List, Dict

from logger_config import logger


class VerificationCodeDetector:
    """验证码检测器"""
    
    # 验证码关键词（中英文）
    KEYWORDS = [
        # 中文关键词
        '验证码', '驗證碼', '动态码', '動態碼', '确认码', '確認碼',
        '安全码', '安全碼', '校验码', '校驗碼', '激活码', '激活碼',
        '验证', '驗證', '校验', '校驗', '激活', '安全',
        # 英文关键词
        'verification code', 'verify code', 'confirmation code',
        'security code', 'otp', 'one-time password', 'pin code',
        'activation code', 'auth code', 'authentication code',
        'dynamic code', 'passcode', 'pin number',
        'verification', 'verify', 'confirm', 'activate', 'authenticate',
        # 常见服务商标识
        'microsoft', 'google', 'apple', 'amazon', 'facebook', 'twitter',
        'github', 'linkedin', 'paypal', 'alipay', 'wechat', 'qq',
        # 其他语言
        'código de verificación',  # 西班牙语
        'code de vérification',    # 法语
        'verificatiecode',         # 荷兰语
    ]
    
    # 验证码正则表达式模式（按优先级排序）
    PATTERNS = [
        # 特殊格式 - 最高优先级（明确标识为验证码）
        r'(?:code|Code|CODE|验证码|驗證碼|验证|驗證|校验|校驗)[:\s是：为為]+([A-Z0-9]{4,8})',
        r'(?:OTP|otp|OTP码|otp码)[:\s]+(\d{4,8})',
        r'(?:您的|your|your\s+)(?:验证码|驗證碼|code|verification\s+code)[:\s是：为為]+([A-Z0-9]{4,8})',
        r'(?:is|为|是|：|:)\s*([A-Z0-9]{4,8})\s*(?:\.|。|,|，|$|请|please)',
        
        # HTML中的验证码（通常被强调）
        r'<b[^>]*>([A-Z0-9]{4,8})</b>',
        r'<strong[^>]*>([A-Z0-9]{4,8})</strong>',
        r'<span[^>]*(?:font-size|font-weight|color|style)[^>]*>([A-Z0-9]{4,8})</span>',
        r'<div[^>]*(?:font-size|font-weight|color|style)[^>]*>([A-Z0-9]{4,8})</div>',
        r'<p[^>]*(?:font-size|font-weight|color|style)[^>]*>([A-Z0-9]{4,8})</p>',
        
        # 纯数字验证码（4-8位）- 常见
        r'(?<!\d)(\d{4,8})(?!\d)',
        
        # 字母数字组合（4-8位，大写优先）
        r'\b([A-Z]{2,4}[0-9]{2,6})\b',  # AB1234
        r'\b([0-9]{2,4}[A-Z]{2,4})\b',  # 1234AB
        r'\b([A-Z0-9]{6})\b',           # 6位大写字母数字
        r'\b([A-Z0-9]{5})\b',           # 5位大写字母数字
        r'\b([A-Z0-9]{7})\b',           # 7位大写字母数字
        
        # 带分隔符的验证码
        r'(\d{3}[-\s]\d{3})',      # 123-456 或 123 456
        r'(\d{2}[-\s]\d{2}[-\s]\d{2})',  # 12-34-56
        r'(\d{4}[-\s]\d{4})',      # 1234-5678
    ]
    
    def __init__(self):
        """初始化检测器"""
        # 编译正则表达式以提高性能
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.PATTERNS]
        logger.info("验证码检测器初始化完成")
    
    def detect(self, subject: str = "", body: str = "") -> Optional[Dict[str, str]]:
        """
        检测邮件中的验证码（只从 body 中检测，忽略 subject）
        
        Args:
            subject: 邮件主题（已废弃，不再使用）
            body: 邮件正文（只检测此内容）
            
        Returns:
            包含验证码信息的字典，如果未找到则返回None
            格式: {"code": "验证码", "location": "body", "context": "上下文"}
        """
        # 只检查 body 是否包含验证码关键词
        if not body:
            return None
        
        has_keyword = any(keyword.lower() in body.lower() for keyword in self.KEYWORDS)
        
        if not has_keyword:
            # 没有关键词，不太可能是验证码邮件
            return None
        
        # 只在正文中查找验证码
        code_info = self._extract_code(body, "body")
        if code_info:
            return code_info
        
        return None
    
    def _extract_code(self, text: str, location: str) -> Optional[Dict[str, str]]:
        """
        从文本中提取验证码
        
        Args:
            text: 要检测的文本
            location: 位置（subject/body）
            
        Returns:
            验证码信息字典或None
        """
        if not text:
            return None
        
        # 清理HTML标签（简单处理）
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        
        # 尝试所有模式
        candidates = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(clean_text)
            if matches:
                for match in matches:
                    # 提取匹配的验证码
                    if isinstance(match, tuple):
                        code = match[0]
                    else:
                        code = match
                    
                    # 验证码基本规则验证
                    if self._is_valid_code(code):
                        # 获取上下文
                        context = self._get_context(text, code)
                        candidates.append({
                            "code": code,
                            "location": location,
                            "context": context
                        })
        
        # 返回最可能的验证码（优先级：靠近关键词的）
        if candidates:
            return self._select_best_candidate(candidates, text)
        
        return None
    
    def _is_valid_code(self, code: str) -> bool:
        """
        验证码基本规则验证
        
        Args:
            code: 候选验证码
            
        Returns:
            是否是有效的验证码
        """
        # 长度检查
        if len(code) < 4 or len(code) > 8:
            return False
        
        # 排除常见的非验证码单词
        exclude_list = [
            'http', 'https', 'www', 'com', 'net', 'org', 'edu', 'gov',
            'mail', 'email', 'dear', 'hello', 'thanks', 'thank',
            'reply', 'subject', 'from', 'sent', 'date', 'time',
            'yyyy', 'dddd', 'mmmm', 'your', 'please', 'click',
            'account', 'password', 'username', 'login', 'security',
            'verification', 'code', 'confirm', 'activate',
            'minute', 'minutes', 'hour', 'hours', 'day', 'days',
            'min', 'sec', 'second', 'seconds',
        ]
        
        if code.lower() in exclude_list:
            return False
        
        # 纯字母且全是小写的可能性很低
        if code.isalpha() and code.islower():
            return False
        
        # 全是同一个字符（如：0000, aaaa）
        if len(set(code)) == 1:
            return False
        
        # 如果是纯字母且长度>6，可能性较低
        if code.isalpha() and len(code) > 6:
            return False
        
        return True
    
    def _get_context(self, text: str, code: str) -> str:
        """
        获取验证码的上下文（前后各30个字符）
        
        Args:
            text: 原始文本
            code: 验证码
            
        Returns:
            上下文字符串
        """
        # 清理HTML
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = ' '.join(clean_text.split())  # 规范化空格
        
        # 查找验证码位置
        pos = clean_text.find(code)
        if pos == -1:
            return ""
        
        # 提取上下文
        start = max(0, pos - 30)
        end = min(len(clean_text), pos + len(code) + 30)
        context = clean_text[start:end]
        
        return context.strip()
    
    def _select_best_candidate(self, candidates: List[Dict[str, str]], text: str) -> Dict[str, str]:
        """
        从多个候选验证码中选择最佳的
        
        Args:
            candidates: 候选验证码列表
            text: 原始文本
            
        Returns:
            最佳候选验证码
        """
        if len(candidates) == 1:
            return candidates[0]
        
        # 评分系统
        scored_candidates = []
        for candidate in candidates:
            score = 0
            code = candidate["code"]
            context = candidate["context"].lower()
            
            # 上下文包含关键词，分数更高
            for keyword in self.KEYWORDS:
                if keyword.lower() in context:
                    score += 10
            
            # 纯数字验证码优先级较高
            if code.isdigit():
                score += 5
            
            # 6位验证码最常见
            if len(code) == 6:
                score += 3
            
            # 大写字母数字组合也常见
            if code.isupper() and any(c.isdigit() for c in code):
                score += 4
            
            scored_candidates.append((score, candidate))
        
        # 按分数排序，返回最高分的
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]
    
    def detect_multiple(self, subject: str = "", body: str = "") -> List[Dict[str, str]]:
        """
        检测邮件中的所有可能的验证码
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            
        Returns:
            验证码信息列表
        """
        all_codes = []
        
        # 检查主题
        text = f"{subject} {body}"
        has_keyword = any(keyword.lower() in text.lower() for keyword in self.KEYWORDS)
        
        if not has_keyword:
            return []
        
        # 在主题和正文中查找所有验证码
        for location, content in [("subject", subject), ("body", body)]:
            if not content:
                continue
            
            clean_text = re.sub(r'<[^>]+>', ' ', content)
            
            for pattern in self.compiled_patterns:
                matches = pattern.findall(clean_text)
                for match in matches:
                    if isinstance(match, tuple):
                        code = match[0]
                    else:
                        code = match
                    
                    if self._is_valid_code(code):
                        # 检查是否已经添加过
                        if not any(c["code"] == code for c in all_codes):
                            context = self._get_context(content, code)
                            all_codes.append({
                                "code": code,
                                "location": location,
                                "context": context
                            })
        
        return all_codes


# 全局单例
_detector = None


def get_detector() -> VerificationCodeDetector:
    """获取验证码检测器单例"""
    global _detector
    if _detector is None:
        _detector = VerificationCodeDetector()
    return _detector


def detect_verification_code(subject: str = "", body: str = "") -> Optional[Dict[str, str]]:
    """
    便捷函数：检测验证码（只从 body 中检测）
    
    Args:
        subject: 邮件主题（已废弃，不再使用）
        body: 邮件正文（只检测此内容，建议使用 body_plain）
        
    Returns:
        验证码信息或None
    """
    detector = get_detector()
    # 只传递 body，忽略 subject
    return detector.detect("", body)


# 测试代码
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        {
            "subject": "Your verification code",
            "body": "Your verification code is: 123456. Please use it within 10 minutes.",
            "expected": "123456"
        },
        {
            "subject": "验证码通知",
            "body": "您的验证码是：<strong>ABC123</strong>，请在5分钟内使用。",
            "expected": "ABC123"
        },
        {
            "subject": "Security Code",
            "body": "Your OTP is 9876. Do not share with anyone.",
            "expected": "9876"
        },
        {
            "subject": "账户激活",
            "body": "激活码：<b>XYZ789</b>",
            "expected": "XYZ789"
        },
    ]
    
    detector = get_detector()
    
    print("=" * 70)
    print("验证码检测器测试")
    print("=" * 70)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"  主题: {case['subject']}")
        print(f"  正文: {case['body']}")
        print(f"  期望: {case['expected']}")
        
        result = detector.detect(case['subject'], case['body'])
        if result:
            print(f"  结果: ✅ 找到验证码 '{result['code']}'")
            print(f"  位置: {result['location']}")
            print(f"  上下文: {result['context']}")
            
            if result['code'] == case['expected']:
                print(f"  匹配: ✅ 正确")
            else:
                print(f"  匹配: ❌ 不匹配（期望: {case['expected']}）")
        else:
            print(f"  结果: ❌ 未找到验证码")
    
    print("\n" + "=" * 70)

