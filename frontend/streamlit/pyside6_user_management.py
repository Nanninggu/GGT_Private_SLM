"""
PySide6 User Management Application
Streamlit user management와 동일한 기능을 PySide6로 구현
"""
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox, 
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QTextEdit,
    QSplitter, QListWidget, QListWidgetItem, QFrame, QScrollArea,
    QHeaderView, QAbstractItemView, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QThread, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

class APIService:
    """API 서비스 클래스 - Streamlit의 APIService와 동일한 기능"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 60
        self.auth_token = None
    
    def set_auth_token(self, token: str):
        """인증 토큰 설정"""
        self.auth_token = token
    
    def get_headers(self):
        """인증 헤더 반환"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    def get_all_users(self) -> Dict[str, Any]:
        """모든 사용자 조회 (관리자만)"""
        try:
            response = requests.get(
                f"{self.base_url}/api/users",
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 사용자 생성 (관리자만)"""
        try:
            response = requests.post(
                f"{self.base_url}/api/users",
                json=user_data,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    return {"success": False, "error": error_data.get("detail", "잘못된 요청입니다.")}
                except:
                    return {"success": False, "error": f"400 Bad Request: {response.text}"}
            elif response.status_code == 403:
                return {"success": False, "error": "관리자 권한이 필요합니다."}
            else:
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 정보 수정 (관리자만)"""
        try:
            response = requests.put(
                f"{self.base_url}/api/users/{user_id}",
                json=user_data,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """사용자 삭제 (관리자만)"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """사용자 로그인"""
        try:
            payload = {
                "username": username,
                "password": password
            }
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": str(e)}

class UserDetailDialog(QDialog):
    """사용자 상세 정보 다이얼로그"""
    
    def __init__(self, user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle(f"사용자 상세 정보 - {user_data.get('username', 'Unknown')}")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_layout = QFormLayout()
        
        basic_layout.addRow("ID:", QLabel(self.user_data.get('id', 'N/A')))
        basic_layout.addRow("사용자명:", QLabel(self.user_data.get('username', 'N/A')))
        basic_layout.addRow("이메일:", QLabel(self.user_data.get('email', 'N/A')))
        basic_layout.addRow("역할:", QLabel(self.user_data.get('role', 'N/A')))
        basic_layout.addRow("상태:", QLabel("활성" if self.user_data.get('is_active', True) else "비활성"))
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 시간 정보 그룹
        time_group = QGroupBox("시간 정보")
        time_layout = QFormLayout()
        
        time_layout.addRow("가입일:", QLabel(self.user_data.get('created_at', 'N/A')))
        time_layout.addRow("수정일:", QLabel(self.user_data.get('updated_at', 'N/A')))
        time_layout.addRow("최근 로그인:", QLabel(self.user_data.get('last_login', 'N/A')))
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class UserEditDialog(QDialog):
    """사용자 정보 수정 다이얼로그"""
    
    def __init__(self, user_data: Dict[str, Any], api_service: APIService, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.api_service = api_service
        self.setWindowTitle(f"사용자 정보 수정 - {user_data.get('username', 'Unknown')}")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # 스타일 설정
        label_style = """
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                font-size: 14px;
            }
        """
        
        input_style = """
            QLineEdit, QComboBox {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """
        
        # 사용자명
        username_label = QLabel("사용자명:")
        username_label.setStyleSheet(label_style)
        self.username_edit = QLineEdit(self.user_data.get('username', ''))
        self.username_edit.setStyleSheet(input_style)
        form_layout.addRow(username_label, self.username_edit)
        
        # 이메일
        email_label = QLabel("이메일:")
        email_label.setStyleSheet(label_style)
        self.email_edit = QLineEdit(self.user_data.get('email', ''))
        self.email_edit.setStyleSheet(input_style)
        form_layout.addRow(email_label, self.email_edit)
        
        # 역할
        role_label = QLabel("역할:")
        role_label.setStyleSheet(label_style)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "user", "guest"])
        self.role_combo.setCurrentText(self.user_data.get('role', 'user'))
        self.role_combo.setStyleSheet(input_style)
        form_layout.addRow(role_label, self.role_combo)
        
        # 상태
        status_label = QLabel("상태:")
        status_label.setStyleSheet(label_style)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["활성", "비활성"])
        self.status_combo.setCurrentText("활성" if self.user_data.get('is_active', True) else "비활성")
        self.status_combo.setStyleSheet(input_style)
        form_layout.addRow(status_label, self.status_combo)
        
        layout.addLayout(form_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        save_btn.clicked.connect(self.save_user)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ 취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_user(self):
        """사용자 정보 저장"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        
        if not username or len(username) < 3:
            QMessageBox.warning(self, "오류", "사용자명은 최소 3자 이상이어야 합니다.")
            return
        
        if not email or '@' not in email:
            QMessageBox.warning(self, "오류", "유효한 이메일 주소를 입력해주세요.")
            return
        
        update_data = {
            "id": self.user_data.get('id'),
            "username": username,
            "email": email,
            "role": self.role_combo.currentText(),
            "is_active": self.status_combo.currentText() == "활성"
        }
        
        result = self.api_service.update_user(self.user_data.get('id'), update_data)
        
        if result.get("success"):
            QMessageBox.information(self, "성공", "사용자 정보가 성공적으로 업데이트되었습니다.")
            self.accept()
        else:
            QMessageBox.critical(self, "오류", f"업데이트 실패: {result.get('error', '알 수 없는 오류')}")

class UserCreateDialog(QDialog):
    """새 사용자 생성 다이얼로그"""
    
    def __init__(self, api_service: APIService, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.setWindowTitle("새 사용자 추가")
        self.setModal(True)
        self.resize(400, 350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 사용자명
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("최소 3자 이상")
        form_layout.addRow("사용자명 *:", self.username_edit)
        
        # 이메일
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@example.com")
        form_layout.addRow("이메일 *:", self.email_edit)
        
        # 비밀번호
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("최소 6자 이상")
        form_layout.addRow("비밀번호 *:", self.password_edit)
        
        # 비밀번호 확인
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("비밀번호를 다시 입력하세요")
        form_layout.addRow("비밀번호 확인 *:", self.confirm_password_edit)
        
        # 역할
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin", "guest"])
        form_layout.addRow("역할:", self.role_combo)
        
        # 활성 상태
        self.is_active_checkbox = QCheckBox("활성 상태")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("", self.is_active_checkbox)
        
        layout.addLayout(form_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("사용자 생성")
        create_btn.clicked.connect(self.create_user)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_user(self):
        """새 사용자 생성"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not username or len(username) < 3:
            QMessageBox.warning(self, "오류", "사용자명은 최소 3자 이상이어야 합니다.")
            return
        
        if ' ' in username:
            QMessageBox.warning(self, "오류", "사용자명에는 공백을 포함할 수 없습니다.")
            return
        
        if not email or '@' not in email:
            QMessageBox.warning(self, "오류", "유효한 이메일 주소를 입력해주세요.")
            return
        
        if not password or len(password) < 6:
            QMessageBox.warning(self, "오류", "비밀번호는 최소 6자 이상이어야 합니다.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "오류", "비밀번호가 일치하지 않습니다.")
            return
        
        user_data = {
            "username": username,
            "email": email,
            "password": password,
            "role": self.role_combo.currentText(),
            "is_active": self.is_active_checkbox.isChecked()
        }
        
        result = self.api_service.create_user(user_data)
        
        if isinstance(result, dict) and result.get("success"):
            QMessageBox.information(self, "성공", "새 사용자가 성공적으로 생성되었습니다.")
            self.accept()
        else:
            error_msg = result.get('message') or result.get('detail') or result.get('error', '알 수 없는 오류')
            QMessageBox.critical(self, "오류", f"생성 실패: {error_msg}")

class UserManagementWidget(QWidget):
    """사용자 관리 위젯"""
    
    def __init__(self, api_service: APIService, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.users = []
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        header_layout = QHBoxLayout()
        title_label = QLabel("👥 사용자 관리")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 새 사용자 추가 버튼
        add_user_btn = QPushButton("➕ 새 사용자 추가")
        add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        add_user_btn.clicked.connect(self.show_create_user_dialog)
        header_layout.addWidget(add_user_btn)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        refresh_btn.clicked.connect(self.load_users)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 사용자 테이블
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(7)
        self.user_table.setHorizontalHeaderLabels([
            "ID", "사용자명", "이메일", "역할", "상태", "가입일", "최근 로그인"
        ])
        
        # 테이블 설정
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 테이블 스타일
        self.user_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.user_table)
        
        # 액션 버튼들
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.view_btn = QPushButton("👁️ 상세 정보")
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover:enabled {
                background-color: #138496;
            }
            QPushButton:pressed:enabled {
                background-color: #117a8b;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.view_btn.clicked.connect(self.view_user_details)
        self.view_btn.setEnabled(False)
        action_layout.addWidget(self.view_btn)
        
        self.edit_btn = QPushButton("✏️ 정보 수정")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover:enabled {
                background-color: #e0a800;
            }
            QPushButton:pressed:enabled {
                background-color: #d39e00;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_user)
        self.edit_btn.setEnabled(False)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ 사용자 삭제")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover:enabled {
                background-color: #c82333;
            }
            QPushButton:pressed:enabled {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_user)
        self.delete_btn.setEnabled(False)
        action_layout.addWidget(self.delete_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # 테이블 선택 이벤트 연결
        self.user_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        self.setLayout(layout)
    
    def load_users(self):
        """사용자 목록 로드"""
        result = self.api_service.get_all_users()
        
        if not result.get("success"):
            QMessageBox.critical(self, "오류", f"사용자 목록을 불러오는 중 오류가 발생했습니다: {result.get('error', '알 수 없는 오류')}")
            return
        
        self.users = result.get("users", [])
        self.update_table()
    
    def update_table(self):
        """테이블 업데이트"""
        self.user_table.setRowCount(len(self.users))
        
        for row, user in enumerate(self.users):
            # ID (축약)
            id_item = QTableWidgetItem(user.get("id", "")[:8] + "...")
            self.user_table.setItem(row, 0, id_item)
            
            # 사용자명
            username_item = QTableWidgetItem(user.get("username", ""))
            self.user_table.setItem(row, 1, username_item)
            
            # 이메일
            email_item = QTableWidgetItem(user.get("email", ""))
            self.user_table.setItem(row, 2, email_item)
            
            # 역할
            role_item = QTableWidgetItem(user.get("role", "user"))
            self.user_table.setItem(row, 3, role_item)
            
            # 상태
            status_item = QTableWidgetItem("활성" if user.get("is_active", True) else "비활성")
            self.user_table.setItem(row, 4, status_item)
            
            # 가입일
            created_at_item = QTableWidgetItem(user.get("created_at", ""))
            self.user_table.setItem(row, 5, created_at_item)
            
            # 최근 로그인
            last_login_item = QTableWidgetItem(user.get("last_login", "없음"))
            self.user_table.setItem(row, 6, last_login_item)
    
    def on_selection_changed(self):
        """선택 변경 이벤트"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.view_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_user(self):
        """선택된 사용자 반환"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        if row < len(self.users):
            return self.users[row]
        return None
    
    def view_user_details(self):
        """사용자 상세 정보 보기"""
        user = self.get_selected_user()
        if user:
            dialog = UserDetailDialog(user, self)
            dialog.exec()
    
    def edit_user(self):
        """사용자 정보 수정"""
        user = self.get_selected_user()
        if user:
            dialog = UserEditDialog(user, self.api_service, self)
            if dialog.exec() == QDialog.Accepted:
                self.load_users()  # 목록 새로고침
    
    def delete_user(self):
        """사용자 삭제"""
        user = self.get_selected_user()
        if not user:
            return
        
        # 확인 다이얼로그
        reply = QMessageBox.question(
            self, 
            "사용자 삭제 확인",
            f"'{user.get('username', 'Unknown')}' 사용자를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.api_service.delete_user(user.get('id'))
            
            if result.get("success"):
                QMessageBox.information(self, "성공", "사용자가 성공적으로 삭제되었습니다.")
                self.load_users()  # 목록 새로고침
            else:
                QMessageBox.critical(self, "오류", f"삭제 실패: {result.get('error', '알 수 없는 오류')}")
    
    def show_create_user_dialog(self):
        """새 사용자 생성 다이얼로그 표시"""
        dialog = UserCreateDialog(self.api_service, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_users()  # 목록 새로고침

class LoginDialog(QDialog):
    """로그인 다이얼로그"""
    
    def __init__(self, api_service: APIService, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.setWindowTitle("로그인")
        self.setModal(True)
        self.resize(300, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("사용자명")
        form_layout.addRow("사용자명:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("비밀번호")
        form_layout.addRow("비밀번호:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("로그인")
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def login(self):
        """로그인 시도"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "오류", "사용자명과 비밀번호를 입력해주세요.")
            return
        
        result = self.api_service.login(username, password)
        
        if result.get("success"):
            # 토큰 저장
            access_token = result.get("access_token")
            if access_token:
                self.api_service.set_auth_token(access_token)
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "로그인 응답에 토큰이 없습니다.")
        else:
            QMessageBox.critical(self, "오류", f"로그인 실패: {result.get('message', '알 수 없는 오류')}")

class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.api_service = APIService()
        self.setWindowTitle("PySide6 User Management")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        
        # 로그인 확인
        self.check_login()
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 이벤트"""
        reply = QMessageBox.question(
            self, 
            "종료 확인",
            "애플리케이션을 종료하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    
    def setup_ui(self):
        """UI 설정"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        
        # 왼쪽 사이드바
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setMinimumWidth(250)
        
        # 사이드바 스타일 설정
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3a3a3a;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #404040;
                color: #00aaff;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
        """)
        
        # 메뉴 아이템들
        self.welcome_item = QListWidgetItem("🏠 홈")
        self.welcome_item.setData(Qt.UserRole, "welcome")
        self.sidebar.addItem(self.welcome_item)
        
        self.user_management_item = QListWidgetItem("👥 User Management")
        self.user_management_item.setData(Qt.UserRole, "user_management")
        self.sidebar.addItem(self.user_management_item)
        
        # 구분선
        separator = QListWidgetItem("")
        separator.setFlags(Qt.NoItemFlags)
        separator.setBackground(QColor("#404040"))
        self.sidebar.addItem(separator)
        
        # 로그아웃 메뉴
        self.logout_item = QListWidgetItem("🚪 로그아웃")
        self.logout_item.setData(Qt.UserRole, "logout")
        self.sidebar.addItem(self.logout_item)
        
        # 사이드바 클릭 이벤트
        self.sidebar.itemClicked.connect(self.on_menu_clicked)
        
        # 첫 번째 아이템 선택
        self.sidebar.setCurrentItem(self.welcome_item)
        
        main_layout.addWidget(self.sidebar)
        
        # 오른쪽 콘텐츠 영역
        self.content_stack = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_stack.setLayout(self.content_layout)
        
        main_layout.addWidget(self.content_stack)
        
        central_widget.setLayout(main_layout)
        
        # 초기 화면
        self.show_welcome_message()
    
    def check_login(self):
        """로그인 확인"""
        dialog = LoginDialog(self.api_service, self)
        if dialog.exec() != QDialog.Accepted:
            self.close()
    
    def on_menu_clicked(self, item):
        """메뉴 클릭 이벤트"""
        menu_type = item.data(Qt.UserRole)
        
        if menu_type == "welcome":
            self.show_welcome_message()
        elif menu_type == "user_management":
            self.show_user_management()
        elif menu_type == "logout":
            self.logout()
    
    def show_welcome_message(self):
        """환영 메시지 표시"""
        self.clear_content()
        
        # 메인 컨테이너
        main_container = QWidget()
        main_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 10px;
                margin: 20px;
            }
        """)
        
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(50, 50, 50, 50)
        
        # 제목
        title_label = QLabel("PySide6 User Management")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)
        
        # 부제목
        subtitle_label = QLabel("Streamlit User Management와 동일한 기능을 PySide6로 구현")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 16px;
                margin-bottom: 30px;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle_label)
        
        # 기능 목록
        features_label = QLabel("""
        <div style="color: white; font-size: 14px; line-height: 1.6;">
            <h3>주요 기능:</h3>
            <ul>
                <li>👥 사용자 목록 조회 및 관리</li>
                <li>➕ 새 사용자 생성</li>
                <li>✏️ 사용자 정보 수정</li>
                <li>🗑️ 사용자 삭제</li>
                <li>👁️ 사용자 상세 정보 확인</li>
            </ul>
            <br>
            <p><strong>사용법:</strong> 왼쪽 사이드바에서 "👥 User Management" 메뉴를 클릭하세요.</p>
        </div>
        """)
        features_label.setAlignment(Qt.AlignLeft)
        container_layout.addWidget(features_label)
        
        container_layout.addStretch()
        main_container.setLayout(container_layout)
        
        self.content_layout.addWidget(main_container)
    
    def logout(self):
        """로그아웃"""
        reply = QMessageBox.question(
            self, 
            "로그아웃 확인",
            "로그아웃하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 토큰 초기화
            self.api_service.set_auth_token(None)
            
            # 로그인 다이얼로그 표시
            dialog = LoginDialog(self.api_service, self)
            if dialog.exec() != QDialog.Accepted:
                self.close()
            else:
                # 홈 화면으로 이동
                self.sidebar.setCurrentItem(self.welcome_item)
                self.show_welcome_message()
    
    def show_user_management(self):
        """사용자 관리 화면 표시"""
        self.clear_content()
        
        user_management_widget = UserManagementWidget(self.api_service)
        self.content_layout.addWidget(user_management_widget)
    
    def clear_content(self):
        """콘텐츠 영역 초기화"""
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')
    
    # 다크 테마 설정
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
