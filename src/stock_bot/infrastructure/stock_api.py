"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: Stock API 客户端，封装了与股票分析系统后端 API 的交互逻辑
"""

from contextlib import suppress
from typing import Optional

import httpx


class StockAPI:
    def __init__(self, base_url: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.password = password
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def login_if_needed(self):
        try:
            status = await self.client.get('/api/v1/auth/status')
            if status.status_code != 200 or not status.json().get('is_logged_in'):
                await self.client.post('/api/v1/auth/login', json={'password': self.password})
        except Exception:
            with suppress(Exception):
                await self.client.post('/api/v1/auth/login', json={'password': self.password})

    async def is_reachable(self) -> bool:
        try:
            r = await self.client.get('/api/v1/auth/status', timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    async def trigger_market_review(self, send_notification: bool = True) -> dict:
        """
        通过 API 触发大盘复盘任务（推荐方式）
        """
        await self.login_if_needed()
        try:
            payload = {'send_notification': send_notification}
            r = await self.client.post('/api/v1/analysis/market-review', json=payload)

            if r.status_code in (200, 202):
                return {'success': True, 'status_code': r.status_code, 'data': r.json()}
            else:
                return {'success': False, 'status_code': r.status_code, 'error': r.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_quote(self, stock_code: str) -> Optional[dict]:
        await self.login_if_needed()
        try:
            r = await self.client.get(f'/api/v1/stocks/{stock_code}/quote')
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    async def get_kline_plot_data(self, stock_code: str, days: int = 120) -> list:
        await self.login_if_needed()
        try:
            r = await self.client.get(
                f'/api/v1/stocks/{stock_code}/history', params={'period': 'daily', 'days': str(days)}
            )
            if r.status_code == 200:
                result = r.json()
                return result.get('data', []) if isinstance(result, dict) else result
            return []
        except Exception:
            return []

    async def get_history(self, limit: int = 50) -> list:
        await self.login_if_needed()
        try:
            r = await self.client.get('/api/v1/history', params={'limit': limit})
            if r.status_code == 200:
                data = r.json()
                return data.get('items', []) if isinstance(data, dict) else data
            return []
        except Exception:
            return []

    async def delete_history(self, record_ids: list):
        await self.login_if_needed()
        try:
            return await self.client.request('DELETE', '/api/v1/history', json={'record_ids': record_ids})
        except Exception:
            return None

    async def analyze(self, code: str, name: str):
        await self.login_if_needed()
        payload = {
            'async_mode': False,
            'force_refresh': False,
            'notify': True,
            'original_query': name,
            'report_type': 'detailed',
            'selection_source': 'autocomplete',
            'stock_code': code,
            'stock_name': name,
        }
        return await self.client.post('/api/v1/analysis/analyze', json=payload)
