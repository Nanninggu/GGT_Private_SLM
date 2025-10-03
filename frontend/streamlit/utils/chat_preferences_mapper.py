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
        
        # 답변 길이에 따른 num_predict 조절 (더 긴 답변을 위해 대폭 증가)
        length_mapping = {
            1: 512,   # 매우 짧게 (256 → 512)
            2: 1024,  # 짧게 (512 → 1024)
            3: 2048,  # 보통 (1024 → 2048)
            4: 3072,  # 자세하게 (2048 → 3072)
            5: 4096   # 매우 자세하게 (4096 → 4096)
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
            "num_predict": length_mapping.get(user_prefs.get("response_length", 3), 1024),
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
        """사용자 설정에 따른 커스텀 시스템 프롬프트 생성"""
        base_prompt = "당신은 도움이 되는 AI 어시스턴트입니다."
        
        # 답변 스타일 설정
        response_style = user_prefs.get("response_style", "자세하게")
        style_instructions = {
            "간결하게": "답변을 간결하고 핵심적으로 작성하세요.",
            "자세하게": "답변을 상세하고 풍부하게 작성하세요.",
            "전문적으로": "전문 용어와 기술적 설명을 포함하여 답변하세요.",
            "친근하게": "일상적이고 이해하기 쉬운 언어로 답변하세요."
        }
        
        # 전문성 수준 설정
        expertise_level = user_prefs.get("expertise_level", "일반인")
        expertise_instructions = {
            "일반인": "일반인도 이해할 수 있도록 쉽게 설명하세요.",
            "중급자": "중간 수준의 전문 용어를 사용하여 설명하세요.",
            "전문가": "고급 전문 용어와 기술적 세부사항을 포함하여 설명하세요."
        }
        
        # 창의성 수준 설정
        creativity_level = user_prefs.get("creativity_level", 3)
        creativity_instructions = {
            1: "보수적이고 안전한 답변을 제공하세요.",
            2: "약간의 창의성을 포함한 답변을 제공하세요.",
            3: "균형잡힌 창의성을 포함한 답변을 제공하세요.",
            4: "창의적이고 다양한 관점의 답변을 제공하세요.",
            5: "매우 창의적이고 독창적인 답변을 제공하세요."
        }
        
        # 프롬프트 조합
        custom_prompt = f"{base_prompt}\n\n"
        custom_prompt += f"답변 스타일: {style_instructions.get(response_style, '')}\n"
        custom_prompt += f"전문성 수준: {expertise_instructions.get(expertise_level, '')}\n"
        custom_prompt += f"창의성 수준: {creativity_instructions.get(creativity_level, '')}\n"
        
        # 한국어 강제 설정
        custom_prompt += "\n반드시 한국어로만 답변하세요."
        
        return custom_prompt
    
    @staticmethod
    def get_user_preferences() -> Dict[str, Any]:
        """현재 사용자 설정을 가져옴"""
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