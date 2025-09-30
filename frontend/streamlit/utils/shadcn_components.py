"""
Shadcn UI Components for Streamlit
"""
import streamlit as st
from streamlit_shadcn_ui import (
    button, card, input, textarea, select, checkbox, radio_group, slider, 
    badges, alert_dialog, avatar, switch, table, tabs, date_picker, 
    metric_card, link_button, hover_card
)
from typing import Any, Dict, List, Optional, Union
import json

class ShadcnComponents:
    """Shadcn UI Components wrapper for Streamlit"""
    
    @staticmethod
    def button(
        text: str,
        variant: str = "default",
        size: str = "default",
        disabled: bool = False,
        loading: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a shadcn-style button"""
        return button(
            text=text,
            variant=variant,
            size=size,
            disabled=disabled,
            loading=loading,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def card(
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[Any] = None,
        variant: str = "default",
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style card"""
        return card(
            title=title,
            description=description,
            content=content,
            variant=variant,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def input(
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        value: str = "",
        disabled: bool = False,
        type: str = "text",
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a shadcn-style input"""
        return input(
            label=label,
            placeholder=placeholder,
            value=value,
            disabled=disabled,
            type=type,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def textarea(
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        value: str = "",
        disabled: bool = False,
        rows: int = 3,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a shadcn-style textarea"""
        return textarea(
            label=label,
            placeholder=placeholder,
            value=value,
            disabled=disabled,
            rows=rows,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def select(
        label: Optional[str] = None,
        options: List[str] = None,
        value: Optional[str] = None,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a shadcn-style select"""
        return select(
            label=label,
            options=options or [],
            value=value,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def checkbox(
        label: str,
        value: bool = False,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a shadcn-style checkbox"""
        return checkbox(
            label=label,
            value=value,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def radio_group(
        label: str,
        options: List[str],
        value: Optional[str] = None,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a shadcn-style radio group"""
        return radio_group(
            label=label,
            options=options,
            value=value,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def slider(
        label: str,
        min_value: float = 0,
        max_value: float = 100,
        value: float = 50,
        step: float = 1,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> float:
        """Create a shadcn-style slider"""
        return slider(
            label=label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=step,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def badge(
        text: str,
        variant: str = "default",
        size: str = "default",
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style badge"""
        return badges(
            text=text,
            variant=variant,
            size=size,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def alert_dialog(
        title: Optional[str] = None,
        description: Optional[str] = None,
        variant: str = "default",
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style alert dialog"""
        return alert_dialog(
            title=title,
            description=description,
            variant=variant,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def tabs(
        tabs: List[Dict[str, Any]],
        default_tab: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create shadcn-style tabs"""
        return tabs(
            tabs=tabs,
            default_tab=default_tab,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def avatar(
        src: Optional[str] = None,
        alt: Optional[str] = None,
        fallback: Optional[str] = None,
        size: str = "default",
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style avatar"""
        return avatar(
            src=src,
            alt=alt,
            fallback=fallback,
            size=size,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def switch(
        label: str,
        value: bool = False,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Create a shadcn-style switch"""
        return switch(
            label=label,
            value=value,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def table(
        data: List[Dict[str, Any]],
        columns: List[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create shadcn-style table"""
        return table(
            data=data,
            columns=columns,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def date_picker(
        label: str,
        value: Optional[str] = None,
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create shadcn-style date picker"""
        return date_picker(
            label=label,
            value=value,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def metric_card(
        title: str,
        value: str,
        description: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style metric card"""
        return metric_card(
            title=title,
            value=value,
            description=description,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def link_button(
        text: str,
        url: str,
        variant: str = "default",
        size: str = "default",
        disabled: bool = False,
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style link button"""
        return link_button(
            text=text,
            url=url,
            variant=variant,
            size=size,
            disabled=disabled,
            key=key,
            **kwargs
        )
    
    @staticmethod
    def hover_card(
        trigger: Any,
        content: Any,
        key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a shadcn-style hover card"""
        return hover_card(
            trigger=trigger,
            content=content,
            key=key,
            **kwargs
        )