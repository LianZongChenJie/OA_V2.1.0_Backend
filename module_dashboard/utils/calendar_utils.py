from enum import Enum
class PlanPriority(Enum):
    """日程优先级枚举"""
    NO = 5  # 无优先级
    LOW = 4  # 不重要
    MEDIUM = 3  # 次要
    HIGH = 2  # 重要
    URGENT = 1  # 紧急

    @property
    def description(self) -> str:
        descriptions = {
            5 : '无优先级',
            4 : '不重要',
            3 : '次要',
            2 : '重要',
            1 : '紧急'
        }
        return descriptions.get(self.value, '未知')

    @property
    def back_ground_colors(self) -> str:
        backGroundColors = {
            5 : '#E9E9CB',
            4 : '#CCEBCC',
            3 : '#D7EBFF',
            2 : '#F6F6C7',
            1 : '#FFD3D3'
        }
        return backGroundColors.get(self.value, 'default')
    @property
    def border_color(self) -> str:
        borderColors = {
            5 : '#CCCC99',
            4 : '#99CC99',
            3 : '#99CCFF',
            2 : '#E8E89B',
            1 : '#FF9999'
        }
        return borderColors.get(self.value, 'default')

from enum import Enum
class SchedulePriority(Enum):
    """工作类别"""
    ANOTHER = 1
    PLAN_FORMULATION = 2
    DOC = 3
    DEMAND_RESEARCH = 4
    Demand_Communication = 5
    MEETING = 6
    CUSTOMER_VISIT = 7
    VISIT_CUSTOM = 8
    RECEPTION_VISIT = 9
    SYSTEM_DESIGN = 10
    SYSTEM_DEVELOPMENT = 11
    SYSTEM_TESTING = 12
    SYSTEM_IMPLEMENT = 13
    SYSTEM_MAINTENANCE = 14
    SYSTEM_ACCEPT = 15

    @property
    def description(self) -> str:
        descriptions = {}

    @property
    def description(self) -> str:
        descriptions = {
            1:'其他',
            2: '方案策划',
            3: '方案撰写',
            4: '需求调研',
            5: '需求沟通',
            6: '参加会议',
            7: '拜访客户',
            8: '接待客户',
            9: '系统设计',
            10: '系统开发',
            11: '系统实施',
            12: '测试验证',
            13: '部署上线',
            14: '系统维护',
            15: '系统验收'
        }
        return descriptions.get(self.value, '未知')

    @property
    def back_ground_colors(self) -> str:
        backGroundColors = {
            15:'#12bb37',
            14:'#12bb37',
            13:'#12bb37',
            12:'#12bb37',
            11:'#12bb37',
            10:'#12bb37',
            6:  "#12bb37",
            5 : '#12bb37',
            4 : '#12bb37',
            3 : '#12bb37',
            2 : '#12bb37',
            1 : '#12bb37'
        }
        return backGroundColors.get(self.value, 'default')
    @property
    def border_color(self) -> str:
        borderColors = {
            15: '#12bb37',
            14: '#12bb37',
            13: '#12bb37',
            12: '#12bb37',
            11: '#12bb37',
            10: '#12bb37',
            6: "#12bb37",
            5: '#12bb37',
            4: '#12bb37',
            3: '#12bb37',
            2: '#12bb37',
            1: '#12bb37'
        }
        return borderColors.get(self.value, 'default')