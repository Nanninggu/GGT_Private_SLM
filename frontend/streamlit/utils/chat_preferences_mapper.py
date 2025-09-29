"""
사용자 채팅 설정을 모델 파라미터로 변환하는 유틸리티
"""
import streamlit as st
from typing import Dict, Any, Optional

class ChatPreferencesMapper:
    """사용자 채팅 설정을 백엔드 모델 파라미터로 변환"""
    
    @staticmethod
    def map_preferences_to_model_config(user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 설정을 모델 설정으로 변환"""
        
        # 답변 길이에 따른 num_predict 조절
        length_mapping = {
            1: 128,   # 매우 짧게
            2: 256,   # 짧게
            3: 512,   # 보통
            4: 1024,  # 자세하게
            5: 2048   # 매우 자세하게
        }
        
        # 정확도 우선순위에 따른 모델 선택
        accuracy_priority = user_prefs.get("accuracy_priority", 4)
        if accuracy_priority >= 4:
            model_type = "quality"  # 고품질 모델
        elif accuracy_priority <= 2:
            model_type = "fast"     # 빠른 모델
        else:
            model_type = "complex"  # 복잡한 모델
        
        # 창의성에 따른 temperature 조절
        creativity_mapping = {
            1: 0.3,   # 보수적
            2: 0.5,   # 약간 창의적
            3: 0.7,   # 보통
            4: 0.8,   # 창의적
            5: 0.9    # 매우 창의적
        }
        
        # 기본 설정
        config = {
            "model_type": model_type,
            "num_predict": length_mapping.get(user_prefs.get("response_length", 3), 512),
            "temperature": creativity_mapping.get(user_prefs.get("creativity_level", 3), 0.7),
            "top_p": 0.9 if user_prefs.get("creativity_level", 3) >= 4 else 0.7,
            "top_k": 50 if user_prefs.get("creativity_level", 3) >= 4 else 20,
            "repeat_penalty": 1.1
        }
        
        # 고급 설정이 활성화된 경우 사용자 지정 값 사용
        if user_prefs.get("use_advanced_settings", False):
            config.update({
                "temperature": user_prefs.get("temperature", config["temperature"]),
                "top_p": user_prefs.get("top_p", config["top_p"]),
                "top_k": user_prefs.get("top_k", config["top_k"]),
                "repeat_penalty": user_prefs.get("repeat_penalty", config["repeat_penalty"])
            })
        
        return config
    
    @staticmethod
    def generate_custom_system_prompt(user_prefs: Dict[str, Any]) -> str:
        """사용자 설정에 따른 시스템 프롬프트 생성"""
        
        base_prompt = "당신은 지식 풍부한 AI 도우미입니다."
        
        # 답변 스타일별 프롬프트
        style_prompts = {
            "간결하게": "답변은 핵심만 간결하게 제공하세요.",
            "자세하게": "답변은 상세하고 구체적으로 제공하세요.",
            "전문적으로": "전문 용어와 정확한 정보를 사용하여 답변하세요.",
            "친근하게": "친근하고 이해하기 쉬운 언어로 답변하세요."
        }
        
        # 정확도 우선순위별 프롬프트
        accuracy_prompts = {
            1: "빠른 응답을 우선시하세요.",
            2: "적당한 속도로 답변하세요.",
            3: "균형 잡힌 답변을 제공하세요.",
            4: "정확성을 우선시하세요.",
            5: "최대한 정확하고 신뢰할 수 있는 정보를 제공하세요."
        }
        
        # 전문성 수준별 프롬프트
        expertise_prompts = {
            "일반인": "일반인이 이해하기 쉬운 수준으로 설명하세요.",
            "중급자": "중급자 수준의 전문 용어와 개념을 포함하여 설명하세요.",
            "전문가": "전문가 수준의 깊이 있는 분석과 전문 용어를 사용하여 설명하세요."
        }
        
        # 답변 길이별 프롬프트
        length_prompts = {
            1: "매우 간결하게 핵심만 답변하세요.",
            2: "간결하게 답변하세요.",
            3: "적당한 길이로 답변하세요.",
            4: "자세하게 답변하세요.",
            5: "매우 상세하고 포괄적으로 답변하세요."
        }
        
        # 프롬프트 조합
        style_prompt = style_prompts.get(user_prefs.get("response_style", "자세하게"), "")
        accuracy_prompt = accuracy_prompts.get(user_prefs.get("accuracy_priority", 4), "")
        expertise_prompt = expertise_prompts.get(user_prefs.get("expertise_level", "일반인"), "")
        length_prompt = length_prompts.get(user_prefs.get("response_length", 3), "")
        
        # 한국어 강제 프롬프트
        korean_prompt = "반드시 한국어로만 답변하세요."
        
        return f"{base_prompt} {style_prompt} {accuracy_prompt} {expertise_prompt} {length_prompt} {korean_prompt}"
    
    @staticmethod
    def get_user_preferences() -> Dict[str, Any]:
        """현재 사용자 설정 가져오기"""
        return st.session_state.get("chat_preferences", {
            "response_style": "자세하게",
            "response_length": 3,
            "accuracy_priority": 4,
            "creativity_level": 3,
            "expertise_level": "일반인",
            "use_advanced_settings": False
        })
    
    @staticmethod
    def apply_preferences_to_chat() -> Dict[str, Any]:
        """현재 설정을 채팅에 적용하고 모델 설정 반환"""
        user_prefs = ChatPreferencesMapper.get_user_preferences()
        model_config = ChatPreferencesMapper.map_preferences_to_model_config(user_prefs)
        system_prompt = ChatPreferencesMapper.generate_custom_system_prompt(user_prefs)
        
        return {
            "model_config": model_config,
            "system_prompt": system_prompt,
            "user_preferences": user_prefs
        }
