from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from module_basicdata.entity.do.public.flow_cate_do import OaFlowCate
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_basicdata.entity.do.public.flow_step_do import OaFlowStep
from module_personnel.entity.do.flow_record_do import OaFlowRecord


class FlowCheckDao:
    """审批流程DAO"""

    @classmethod
    async def get_flow_cate_by_name(cls, db: AsyncSession, name: str) -> OaFlowCate | None:
        """根据名称获取审批类型"""
        query = select(OaFlowCate).where(
            OaFlowCate.name == name,
            OaFlowCate.status == 1
        )
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_flow_by_id(cls, db: AsyncSession, flow_id: int) -> OaFlow | None:
        """根据ID获取流程"""
        query = select(OaFlow).where(OaFlow.id == flow_id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def add_flow_step(cls, db: AsyncSession, step_data: dict) -> OaFlowStep:
        """添加审批步骤"""
        db_model = OaFlowStep(**step_data)
        db.add(db_model)
        return db_model

    @classmethod
    async def add_flow_record(cls, db: AsyncSession, record_data: dict) -> OaFlowRecord:
        """添加审批记录"""
        db_model = OaFlowRecord(**record_data)
        db.add(db_model)
        return db_model

    @classmethod
    async def update_business_table(cls, db: AsyncSession, check_table: str, action_id: int, update_data: dict):
        """更新业务表审批状态"""
        table_name = check_table if check_table.startswith('oa_') else f'oa_{check_table}'
        set_clauses = [f"{key} = :{key}" for key in update_data.keys()]
        sql = f"UPDATE `{table_name}` SET {', '.join(set_clauses)} WHERE id = :action_id"
        await db.execute(text(sql), {**update_data, 'action_id': action_id})

    @classmethod
    async def delete_old_steps(cls, db: AsyncSession, action_id: int, flow_id: int, delete_time: int):
        """删除旧的审批步骤"""
        await db.execute(
            text("""
                UPDATE oa_flow_step 
                SET delete_time = :delete_time 
                WHERE action_id = :action_id 
                  AND flow_id = :flow_id 
                  AND delete_time = 0
            """),
            {'delete_time': delete_time, 'action_id': action_id, 'flow_id': flow_id}
        )

    @classmethod
    async def delete_old_records(cls, db: AsyncSession, action_id: int, check_table: str, delete_time: int):
        """删除旧的审批记录"""
        await db.execute(
            text("""
                UPDATE oa_flow_record 
                SET delete_time = :delete_time 
                WHERE action_id = :action_id 
                  AND check_table = :check_table 
                  AND delete_time = 0
            """),
            {'delete_time': delete_time, 'action_id': action_id, 'check_table': check_table}
        )

    @classmethod
    async def get_current_step(cls, db: AsyncSession, action_id: int, flow_id: int, sort: int) -> dict | None:
        """获取当前审批步骤"""
        result = await db.execute(
            text("""
                SELECT * FROM oa_flow_step 
                WHERE action_id = :action_id 
                  AND flow_id = :flow_id 
                  AND sort = :sort 
                  AND delete_time = 0
                LIMIT 1
            """),
            {'action_id': action_id, 'flow_id': flow_id, 'sort': sort}
        )
        row = result.first()
        return dict(row._mapping) if row else None

    @classmethod
    async def get_department_leader(cls, db: AsyncSession, uid: int, level: int = 0) -> str:
        """获取部门负责人"""
        dept_result = await db.execute(
            text("SELECT did, leader_ids FROM oa_admin WHERE id = :uid"),
            {'uid': uid}
        )
        dept_row = dept_result.first()
        
        if not dept_row:
            return ''
        
        did = dept_row[0]
        leader_ids = dept_row[1]
        
        if level == 1:
            parent_result = await db.execute(
                text("SELECT parent_id FROM oa_dept WHERE id = :did"),
                {'did': did}
            )
            parent_row = parent_result.first()
            
            if parent_row and parent_row[0]:
                parent_leader_result = await db.execute(
                    text("SELECT leader_ids FROM oa_dept WHERE id = :parent_did"),
                    {'parent_did': parent_row[0]}
                )
                parent_leader_row = parent_leader_result.first()
                
                if parent_leader_row and parent_leader_row[0]:
                    return parent_leader_row[0]
        
        return leader_ids or ''

    @classmethod
    async def send_message(cls, db: AsyncSession, from_uid: int, uids: str, 
                          template: str, action_id: int, content: str, send_time: int):
        """发送消息"""
        await db.execute(
            text("""
                INSERT INTO oa_message 
                (title, template, content, from_uid, types, uids, is_draft, send_time, create_time, action_id)
                VALUES (:title, :template, :content, :from_uid, :types, :uids, :is_draft, :send_time, :create_time, :action_id)
            """),
            {
                'title': '',
                'template': template,
                'content': content,
                'from_uid': from_uid,
                'types': 1,
                'uids': uids,
                'is_draft': 1,
                'send_time': send_time,
                'create_time': send_time,
                'action_id': action_id
            }
        )
