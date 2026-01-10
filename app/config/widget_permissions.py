from typing import List, Dict, Optional
from enum import Enum

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"

class WidgetPermission:
    """
    Konfigurasi permissions untuk widget dashboard
    """
    # Widget permissions configuration
    WIDGET_PERMISSIONS: Dict[str, List[UserRole]] = {
        # Monitoring Widgets
        "invoice_generation_monitor": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],
        "future_invoice_projection": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],

        # Financial Widgets
        "revenue_summary": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],

        # Customer Analytics
        "customer_stats": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],
        "lokasi_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],
        "paket_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],
        "growth_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],
        "status_langganan_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],
        "loyalitas_pembayaran_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],
        "alamat_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],

        # Server/System Widgets
        "server_stats": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN
        ],
        "invoice_summary_chart": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ]
    }

    # Category-based permissions
    CATEGORY_PERMISSIONS: Dict[str, List[UserRole]] = {
        "monitoring": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],
        "financial": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER
        ],
        "analytics": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.STAFF
        ],
        "system": [
            UserRole.SUPERADMIN,
            UserRole.ADMIN
        ]
    }

    @classmethod
    def can_access_widget(cls, widget_name: str, user_role: str) -> bool:
        """
        Check if user can access specific widget
        """
        # Try to get widget-specific permission
        if widget_name in cls.WIDGET_PERMISSIONS:
            return UserRole(user_role.lower()) in cls.WIDGET_PERMISSIONS[widget_name]

        # Check by category if widget not found
        for category, widgets in {
            "monitoring": ["invoice_generation_monitor", "future_invoice_projection"],
            "financial": ["revenue_summary", "invoice_summary_chart"],
            "analytics": ["customer_stats", "lokasi_chart", "paket_chart", "growth_chart",
                         "status_langganan_chart", "loyalitas_pembayaran_chart", "alamat_chart"],
            "system": ["server_stats"]
        }.items():
            if widget_name in widgets:
                return UserRole(user_role.lower()) in cls.CATEGORY_PERMISSIONS.get(category, [])

        # Default: allow access to admins and above
        return UserRole(user_role.lower()) in [UserRole.SUPERADMIN, UserRole.ADMIN]

    @classmethod
    def get_widget_config(cls, widget_name: str) -> Dict:
        """
        Get widget configuration including required role level
        """
        config = {
            "name": widget_name,
            "required_roles": [],
            "category": None,
            "description": ""
        }

        # Set category based on widget
        if widget_name in ["invoice_generation_monitor", "future_invoice_projection"]:
            config["category"] = "monitoring"
            config["description"] = "Monitoring invoice generation"
        elif widget_name in ["revenue_summary", "invoice_summary_chart"]:
            config["category"] = "financial"
            config["description"] = "Financial data and reports"
        elif widget_name in ["server_stats"]:
            config["category"] = "system"
            config["description"] = "System and server statistics"
        else:
            config["category"] = "analytics"
            config["description"] = "Customer and business analytics"

        # Get required roles
        if widget_name in cls.WIDGET_PERMISSIONS:
            config["required_roles"] = [role.value for role in cls.WIDGET_PERMISSIONS[widget_name]]
        elif config["category"] in cls.CATEGORY_PERMISSIONS:
            config["required_roles"] = [role.value for role in cls.CATEGORY_PERMISSIONS[config["category"]]]

        return config

    @classmethod
    def get_user_widgets(cls, user_role: str) -> List[str]:
        """
        Get list of widgets user can access based on their role
        """
        accessible_widgets = []

        # Check each widget permission
        for widget_name in cls.WIDGET_PERMISSIONS.keys():
            if cls.can_access_widget(widget_name, user_role):
                accessible_widgets.append(widget_name)

        return accessible_widgets